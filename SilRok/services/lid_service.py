import asyncio
import numpy as np

from dataclasses import dataclass, field
from typing import Awaitable, Callable, overload, TypeAlias, Optional
from typing_extensions import override, Self
from dependency_injector.resources import AsyncResource
from logging import Logger

from LID import LID, SpeakerSentence
from sjpy.audio import generate_empty_chunk

StreamCallback: TypeAlias = Callable[
    [Optional["LIDSentence"], Optional[Exception]], Awaitable[None]
]
EmbedCallback: TypeAlias = Callable[
    [Optional[np.ndarray], Optional[Exception]], Awaitable[None]
]


@dataclass(slots=True, frozen=True)
class Embedding:
    uid: str
    embedding: np.ndarray


@dataclass(slots=True, frozen=True)
class LIDSentence:
    gid: str
    completed: list[SpeakerSentence]
    candidate: list[SpeakerSentence]


@dataclass
class User:
    uid: str = field(compare=True)
    group: "Group" = field(compare=False)
    just_me: bool = field(compare=False)  # 화자 분리 없이, 소스 오디오 = 화자일 경우
    chunk: np.ndarray = field(default_factory=generate_empty_chunk, compare=False)
    # 여기 콜백 등록하는게 별로긴한데, 요청마다 응답이 가는게 아니기 때문에, 어쩔 수 없다.
    callback: StreamCallback | None = field(default=None, compare=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False, compare=False)
    last_seen: float = field(
        default_factory=asyncio.get_event_loop().time, compare=False
    )

    def __hash__(self):
        return hash(self.uid)


@dataclass
class Group:
    gid: str = field(compare=True)
    users: set[User] = field(
        default_factory=set, init=False, compare=False
    )  # 그룹에 속한 유저
    embedding_uids: list[str] = field(
        default_factory=list, init=False, compare=False
    )  # 화자 분리할 유저 리스트 (순서 = embeddings 순서)
    embeddings: np.ndarray | None = field(default=None, repr=False, compare=False)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock, repr=False, compare=False)

    def __hash__(self):
        return hash(self.gid)


class LIDService(AsyncResource):
    # NOTE 임시로 N초 비활성 사용자 정리 기능 추가
    # NOTE delete 요청이 있다면, 코드 더 간결해짐
    def __init__(
        self,
        logger: Logger,
        diarizer_job_num: int,
        asr_job_num: int,
        minimum_chunk_duration: int,
        inactive_sec: int = 600,
        broker_options: dict = None,
        diarizer_options: dict = None,
        asr_options: dict = None,
    ):
        super().__init__()
        self.logger = logger
        self.lid = LID(diarizer_job_num=diarizer_job_num, asr_job_num=asr_job_num)
        self.users: dict[str, User] = {}
        self.groups: dict[str, Group] = {}
        self.__mcd = minimum_chunk_duration
        self.__lock = asyncio.Lock()
        self.__reaper_task = None
        self.__inactive_sec = inactive_sec

        self.__init_broker_options = broker_options
        self.__init_diarizer_options = diarizer_options
        self.__init_asr_options = asr_options

    @override
    async def init(self, *_, **__) -> Self:
        await super().init()

        await self.lid.init(
            broker_options=self.__init_broker_options,
            diarizer_options=self.__init_diarizer_options,
            asr_options=self.__init_asr_options,
        )
        self.__reaper_task = asyncio.create_task(self.__reap_inactive_users())
        return self

    @override
    async def shutdown(self, _: Self):
        if self.__reaper_task is not None:
            self.__reaper_task.cancel()
            try:
                await self.__reaper_task
            except asyncio.CancelledError:
                pass
            self.__reaper_task = None

        await super().shutdown(_)
        await self.lid.close()

    async def ensure_group(self, gid: str) -> Group:
        group = self.groups.get(gid)
        if group is not None:
            return group
        async with self.__lock:
            if gid in self.groups:
                return self.groups[gid]
            await self.lid.register_group(gid)
            group = Group(gid=gid)
            self.groups[gid] = group
            return group

    async def ensure_user(
        self,
        gid: str,
        uid: str,
        just_me: bool,
        initial_offset: int = 0,
        callback: StreamCallback | None = None,
    ) -> User:
        group = await self.ensure_group(gid)
        user = self.users.get(uid)
        if user is not None:
            return user
        async with self.__lock:
            if uid in self.users:
                return self.users[uid]
            user = User(uid=uid, group=group, just_me=just_me, callback=callback)

            async with group.lock:
                if just_me:
                    await self.lid.register_user(uid, None, initial_offset)
                else:
                    await self.lid.register_user(uid, gid, initial_offset)

                group.users.add(user)
                self.users[uid] = user
            return user

    async def delete_group(self, gid: str) -> None:
        group = self.groups.get(gid)
        if group is None:
            raise ValueError(f"Group {gid} does not exist")
        async with self.__lock:
            async with group.lock:
                if len(group.users) > 0:
                    raise ValueError(f"Group {gid} is not empty")
                await self.lid.unregister_group(gid)
                del self.groups[gid]

    @overload
    async def delete_user(self, uid: str) -> LIDSentence: ...
    @overload
    async def delete_user(self, uid: str, callback: StreamCallback) -> None: ...
    async def delete_user(
        self, uid: str, callback: StreamCallback | None = None
    ) -> None | LIDSentence:
        user = self.users.get(uid)
        if user is None:
            raise ValueError(f"User {uid} does not exist")
        async with self.__lock:
            result = None
            async with user.group.lock:
                # embedding_users는 사용자 삭제와 무관하게 유지
                user.group.users.remove(user)
                async with user.lock:
                    if callback is None:
                        completed, candidate = await self.lid.unregister_user(uid)
                        result = LIDSentence(
                            gid=user.group.gid, completed=completed, candidate=candidate
                        )
                    else:
                        self.lid.unregister_user_callback(uid, callback)
            del self.users[uid]
            return result

    @overload
    async def embedding(self, uid: str, chunk: np.ndarray) -> Embedding: ...
    @overload
    async def embedding(
        self, uid: str, chunk: np.ndarray, callback: EmbedCallback
    ) -> None: ...
    async def embedding(
        self, uid: str, chunk: np.ndarray, callback: EmbedCallback | None = None
    ) -> None | Embedding:
        # 단순히 임베딩만 반환하기 때문에 유저 따로 안만듬
        if chunk.ndim == 1:
            chunk = chunk.reshape(1, -1, 1)
        elif chunk.ndim == 2:
            chunk = chunk.reshape(1, -1, chunk.shape[0])

        if callback:
            self.lid.embedding_callback(chunk, self._embed_callback(uid, callback))
        else:
            embedding = await self.lid.embedding_wait(chunk)
            return Embedding(uid=uid, embedding=embedding)

    @overload
    async def update_embedding(
        self, gid: str, embeddings_members: list[str], embeddings: np.ndarray
    ) -> None: ...
    async def update_embedding(
        self,
        gid: str,
        embeddings_members: list[str],
        embeddings: np.ndarray,
    ) -> None:
        if embeddings.ndim != 2 or embeddings.shape[0] != len(embeddings_members):
            raise ValueError("Embeddings count does not match embeddings_members count")
        group = await self.ensure_group(gid)

        for uid in embeddings_members:
            user = self.users.get(uid)
            if user is None:
                continue
            if user.group.gid != gid:
                raise ValueError(
                    f"User {uid} does not belong to group {gid}, cannot update embeddings"
                )
            if user.just_me:
                raise ValueError(f"User {uid} is 'just_me', cannot update embeddings")

        async with group.lock:
            group.embedding_uids = embeddings_members
            group.embeddings = embeddings
            await self.lid.set_embedding_wait(gid, embeddings_members, embeddings)

    @overload
    async def run(self, chunk: np.ndarray) -> LIDSentence: ...
    @overload
    async def run(self, chunk: np.ndarray, callback: StreamCallback) -> None: ...
    @overload
    async def run(self, chunk: np.ndarray, language: str) -> LIDSentence: ...
    @overload
    async def run(
        self, chunk: np.ndarray, language: str, callback: StreamCallback
    ) -> None: ...
    async def run(
        self,
        chunk: np.ndarray,
        language: str | None = None,
        callback: StreamCallback | None = None,
    ) -> None | LIDSentence:
        """
        단순 ASR 실행
        """
        if callback:
            callback = self._run_asr_callback(callback)
            self.lid.run_asr_callback(chunk, callback, language)
        else:
            result = await self.lid.run_asr(chunk, language)
            return LIDSentence(gid="", completed=result, candidate=[])

    @overload
    async def stream(
        self,
        gid: str,
        uid: str,
        chunk: np.ndarray | None,
        initial_offset: int | None,
        language: str | None,
    ) -> LIDSentence: ...
    @overload
    async def stream(
        self,
        gid: str,
        uid: str,
        chunk: np.ndarray | None,
        initial_offset: int | None,
        language: str | None,
        callback: StreamCallback,
    ) -> None: ...
    async def stream(
        self,
        gid: str,
        uid: str,
        chunk: np.ndarray | None,
        initial_offset: int | None = None,
        language: str | None = None,
        callback: StreamCallback | None = None,
    ) -> LIDSentence | None:
        """
        1. chunk: None이면 스트림 종료 신호
        2. 유저가 없으면 생성
            2.1. 그룹에 유저의 임베딩 벡터를 가지고 있으면, 유저는 just_me=False로 생성
            2.2. 그룹에 유저의 임베딩 벡터가 있으면, 유저 만들고 임베딩 벡터 다시 적용
            2.3. 없으면 just_me=True로 생성
        3. 스트림 처리
        4. 스트림 종료 신호면 유저 삭제
        5. 콜백이 있으면 콜백으로 결과 전달, 없으면 결과 반환
        """

        # NOTE 화자분리 성능이 별로면, 임베딩 업데이트 시, 그룹 재등록 시도해볼 것
        callback = (
            callback if callback is None else self._stream_callback(gid, callback)
        )
        if uid not in self.users:
            initial_offset = initial_offset or 0
            group = await self.ensure_group(gid)
            if uid in group.embedding_uids:
                # 사용자 등록 후 임베딩 전체  재등록
                await self.ensure_user(gid, uid, False, initial_offset, callback)
                await self.lid.set_embedding_wait(
                    gid, group.embedding_uids, group.embeddings
                )
            else:
                await self.ensure_user(gid, uid, True, initial_offset, callback)

        user = self.users[uid]

        if callback is None:
            stream = self.lid.stream_asr if user.just_me else self.lid.stream
        else:
            stream = (
                self.lid.stream_asr_callback
                if user.just_me
                else self.lid.stream_callback
            )

        async with user.lock:
            user.last_seen = asyncio.get_event_loop().time()
            if chunk is None:
                chunk, user.chunk, end = user.chunk, generate_empty_chunk(), True
            else:
                user.chunk, end = np.concatenate((user.chunk, chunk), axis=0), False
                if user.chunk.shape[0] > self.__mcd:
                    chunk, user.chunk = (
                        user.chunk[: self.__mcd],
                        user.chunk[self.__mcd :],
                    )
                elif callback is None:
                    return LIDSentence(gid=gid, completed=[], candidate=[])
                else:
                    return

            if callback is None:
                completed, candidate = await stream(uid, chunk, language)
            else:
                stream(uid, chunk, callback, language)

        if callback is None:
            result = LIDSentence(gid=gid, completed=completed, candidate=candidate)
            if end:
                end_result = await self.delete_user(uid)
                result.completed.extend(end_result.completed)
                result.candidate.extend(end_result.candidate)
            return result

        if end:
            await self.delete_user(uid, callback)

    def _run_asr_callback(self, callback: StreamCallback):
        async def wrapped(c: list[SpeakerSentence] | None, err: Exception | None):
            if err is not None:
                await callback(None, err)
            else:
                await callback(LIDSentence(gid="", completed=c, candidate=[]), None)

        return wrapped

    def _stream_callback(self, gid: str, callback: StreamCallback):
        async def wrapped(
            result: tuple[list[SpeakerSentence], list[SpeakerSentence]] | None,
            err: Exception | None,
        ):
            if err is not None:
                await callback(None, err)
            else:
                await callback(
                    LIDSentence(gid=gid, completed=result[0], candidate=result[1]), None
                )

        return wrapped

    def _embed_callback(self, uid: str, callback: EmbedCallback):
        async def wrapped(emb: np.ndarray | None, err: Exception | None):
            if err is not None:
                await callback(None, err)
            else:
                await callback(Embedding(uid, emb), None)

        return wrapped

    async def __reap_inactive_users(self):
        while True:
            await asyncio.sleep(self.__inactive_sec)
            now = asyncio.get_event_loop().time()
            async with self.__lock:
                inactive_uids = [
                    user
                    for user in self.users.values()
                    if now - user.last_seen > self.__inactive_sec
                ]
            for user in inactive_uids:
                try:
                    await self.delete_user(user.uid, user.callback)
                except Exception:
                    pass


__all__ = ["LIDService", "Embedding", "LIDSentence"]
