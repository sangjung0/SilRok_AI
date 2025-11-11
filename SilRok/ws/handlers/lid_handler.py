from __future__ import annotations
from typing import TYPE_CHECKING

from joblib import Logger
import numpy as np

from typing import Callable, Any, Awaitable
from dataclasses import dataclass
from functools import cached_property

from sjpy.audio import mp4_bytes_to_ndarray, s16le_bytes_to_array, resample_wav

from SilRok.services import LIDService, Embedding, LIDSentence
from SilRok.ws.session import Session, Payload, FLAGS
from SilRok.core import config
from SilRok.utils import embedding_from_bytes

if TYPE_CHECKING:
    pass

LID_EMBED = "diarization_embed"
LID_REFER = "diarization_refer"
LID = "diarization"
LID_FLAGS = set(
    [
        LID_EMBED,
        LID_REFER,
        LID,
    ]
)

SAMPLE_RATE = config.service.common.sample_rate
EMBEDDING_LENGTH = config.service.common.embedding_length
MIN_DURATION = config.service.lid_service.minimum_chunk_duration


@dataclass(frozen=True)
class LIDPayload:
    payload: Payload

    @property
    def flag(self):
        return self.payload.flag

    @cached_property
    def gid(self):
        return self.payload.metadata["group_id"]

    @cached_property
    def uid(self):
        return self.payload.metadata["user_id"]

    @cached_property
    def uids(self):
        return self.payload.metadata.get("user_ids", [])

    @cached_property
    def counts(self):
        return self.payload.metadata.get("counts", [])

    @cached_property
    def sc_offset(self):
        return self.payload.metadata.get("sc_offset", None)

    @cached_property
    def language(self):
        return self.payload.metadata.get("language", None)

    @cached_property
    def sample_rate(self):
        return self.payload.metadata.get("sample_rate", SAMPLE_RATE)

    @cached_property
    def audio(self) -> np.ndarray | None:
        if self.flag == LID_EMBED:
            if len(self.payload.data) == 0:
                raise ValueError("No refer data found in metadata payload")
            audio = mp4_bytes_to_ndarray(self.payload.data, SAMPLE_RATE)
            if audio.shape[0] < MIN_DURATION:
                raise ValueError(
                    f"Audio length {audio.shape[0]} is less than minimum required duration {MIN_DURATION}"
                )
        else:
            # 흠
            if len(self.payload.data) == 0:
                return None
            # NOTE 스마트폰 PCM 16-bit 48kHz로 되어있음. 여전히 PCM 16-bit인데 16HZ로 변경해서 보냄. 또 변경해야함.
            # NOTE 만약 음성 인식 제대로 안되면 여기 바꿔보자
            audio = s16le_bytes_to_array(self.payload.data)
            audio = resample_wav(audio, self.sample_rate, SAMPLE_RATE).reshape(-1)
        return audio

    @cached_property
    def embeddings(self) -> tuple[list[str], np.ndarray]:
        length = len(self.payload.data)
        if length == 0:
            raise ValueError("No refer data found in metadata payload")

        embedding = embedding_from_bytes(
            self.payload.data, self.counts, EMBEDDING_LENGTH
        )

        return self.uids, embedding

    @staticmethod
    def from_payload(payload: Payload) -> LIDPayload:
        return LIDPayload(payload=payload)


class LIDHandler:
    def __init__(self, logger: Logger, lid_service: LIDService):
        for flag in LID_FLAGS:
            FLAGS.add(flag)

        assert isinstance(
            lid_service, LIDService
        ), "lid_service must be an instance of LIDService"

        self.logger = logger
        self.lid_service = lid_service
        self.__callbacks: dict[str, dict[str, Callable]] = {}

    def get_callbacks(self, sid: str) -> dict[str, Callable]:
        return self.__callbacks[sid]

    def del_callbacks(self, sid: str) -> None:
        if sid in self.__callbacks:
            del self.__callbacks[sid]

    def set_callbacks(self, sid: str, callbacks: dict[str, Callable]) -> None:
        self.__callbacks[sid] = callbacks

    async def on_disconnect(self, session: Session, sid: str):
        self.del_callbacks(sid)

    async def on_connect(
        self, session: Session, sid: str
    ) -> tuple[Callable[[bytes], Awaitable[None]], dict[str, Callable]]:
        async def send(data: bytes):
            await session.send_bytes(sid, data)

        dumps = session.get_serializer(sid)["dumps"]
        callbacks = {
            LID_EMBED: self._lid_embed_callback(send, dumps),
            LID: self._lid_stream_callback(send, dumps),
        }
        self.set_callbacks(sid, callbacks)

        return send, callbacks

    async def on_metadata(self, session: Session, sid: str, payload: Payload) -> bool:
        flag = payload.flag
        if flag not in LID_FLAGS:
            return False

        lp = LIDPayload.from_payload(payload)
        if flag == LID_EMBED:
            callback = self.get_callbacks(sid)[LID_EMBED]
            await self.lid_service.embedding(lp.uid, lp.audio, callback)
            return True
        elif flag == LID_REFER:
            uids, embeddings = lp.embeddings
            callback = self.get_callbacks(sid)[
                LID
            ]  # NOTE 임시로 나둠. delete 요청 생기면 지워도 됨
            await self.lid_service.update_embedding(lp.gid, uids, embeddings)
            return True
        elif flag == LID:
            callback = self.get_callbacks(sid)[LID]
            await self.lid_service.stream(
                lp.gid, lp.uid, lp.audio, lp.sc_offset, lp.language, callback
            )
            return True
        return False

    def _lid_stream_callback(
        self, send: Callable[[bytes], Awaitable[None]], dumps: Callable[[Any], bytes]
    ):
        from SilRok.dto.response import LIDResponse, ErrorResponse

        async def callback(Y: LIDSentence | None, err: Exception | None):
            if err is not None:
                self.logger.error(f"Error in lid stream callback:\n\t{err}")
                await send(ErrorResponse(error=str(err)).to_bytes(dumps))
                return

            if Y is not None:
                self.logger.info(
                    f"completed: {[(speak.order, speak.text) for speak in Y.completed]}\n-candidate: {[(speak.order, speak.text) for speak in Y.candidate]}"
                )

                await send(LIDResponse.from_lid_sentence(Y).to_bytes(dumps))

        return callback

    def _lid_embed_callback(
        self, send: Callable[[bytes], Awaitable[None]], dumps: Callable[[Any], bytes]
    ):
        from SilRok.dto.response import LIDEmbedResponse, ErrorResponse

        async def callback(Y: Embedding | None, e: Exception | None):
            if e is not None:
                self.logger.error(f"Error in lid embed callback:\n\t{e}")
                await send(ErrorResponse(error=str(e)).to_bytes(dumps))
                return
            if Y is not None:
                await send(LIDEmbedResponse.from_embedding(Y).to_bytes(dumps))

        return callback


__all__ = ["LID_EMBED", "LID_REFER", "LID", "LID_FLAGS", "LIDHandler", "LIDPayload"]
