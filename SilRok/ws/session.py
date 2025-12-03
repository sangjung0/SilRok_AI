import json
import uuid
import msgpack
import asyncio

from typing import Callable, Awaitable
from typing_extensions import Self
from dataclasses import dataclass
from functools import cached_property
from collections import defaultdict
from logging import Logger
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.websockets import WebSocketState

from sjpy.excptn import exc_to_str

from SilRok.dto.response import ErrorResponse

OnMetadata = Callable[[Self, str, "Payload"], Awaitable[None]]
OnConnect = Callable[[Self, str], Awaitable[None]]
OnDisconnect = Callable[[Self, str], Awaitable[None]]

MSGPACK = "msgpack"
JSON = "json"
TYPES = [MSGPACK, JSON]
FLAGS = set()

serializer_default = {
    MSGPACK: {"dumps": msgpack.dumps, "loads": msgpack.loads},
    JSON: {
        "dumps": lambda x: json.dumps(x).encode("utf-8"),
        "loads": lambda x: json.loads(x.decode("utf-8")),
    },
}


@dataclass(frozen=True)
class Payload:
    metadata: dict
    data: bytes

    @cached_property
    def flag(self) -> str:
        return self.metadata["flag"]

    @cached_property
    def group_id(self) -> str:
        return self.metadata["group_id"]

    @staticmethod
    def from_bytes(data: bytes, loads: Callable[[bytes], dict]) -> Self:
        metadata, data = Payload.byte_to_dict(data, loads)
        if metadata["flag"] not in FLAGS:
            raise ValueError(f"Invalid flag: {metadata['flag']}")

        return Payload(metadata=metadata, data=data)

    @staticmethod
    def byte_to_dict(data: bytes, loads: Callable[[bytes], dict]) -> tuple[dict, bytes]:
        end = 4 + int.from_bytes(data[0:4], byteorder="big")
        return loads(data[4:end]), data[end:]


class Session:
    def __init__(
        self,
        logger: Logger,
        max_connection: int,
        max_send_queue_size: int,
        serializer: dict[str, dict[str, Callable]] | None = None,
    ):
        if not isinstance(logger, Logger):
            raise TypeError("logger must be an instance of logging.Logger")
        if not isinstance(max_connection, int) or max_connection <= 0:
            raise ValueError("max_connection must be a positive integer")

        super().__init__()
        self.logger = logger
        self.serializer = serializer or serializer_default
        self.__send_qs: dict[str, asyncio.Queue[bytes | None]] = defaultdict(
            lambda: asyncio.Queue(maxsize=max_send_queue_size)
        )
        self.__available_connections = max_connection

        self.__pack_func = {}
        self.__on_metadata_handlers: dict[
            str, Callable[[Self, str, Payload], Awaitable[None]]
        ] = {}
        self.__on_connect_handlers: dict[
            str, Callable[[Self, str], Awaitable[None]]
        ] = {}
        self.__on_disconnect_handlers: dict[
            str, Callable[[Self, str], Awaitable[None]]
        ] = {}
        self.__events: dict[str, asyncio.Event] = {}

    @property
    def available_connections(self) -> int:
        return self.__available_connections

    def increase_available_connections(self, n: int = 1) -> None:
        self.__available_connections += n

    def decrease_available_connections(self, n: int = 1) -> None:
        self.__available_connections -= n

    def get_serializer(self, sid: str) -> dict[str, Callable]:
        return self.__pack_func[sid]

    def set_serializer(self, sid: str, typ: str) -> None:
        self.__pack_func[sid] = self.serializer[typ]

    def del_serializer(self, sid: str) -> None:
        del self.__pack_func[sid]

    async def send_bytes(self, sid: str, data: bytes) -> None:
        await self.__send_qs[sid].put(data)

    def get_send_queue(self, sid: str) -> asyncio.Queue[bytes | None]:
        return self.__send_qs[sid]

    def del_send_queue(self, sid: str) -> None:
        del self.__send_qs[sid]

    def attach_on_metadata(self, sid: str, handler: OnMetadata) -> None:
        self.__on_metadata_handlers[sid] = handler

    def attach_on_connect(self, sid: str, handler: OnConnect) -> None:
        self.__on_connect_handlers[sid] = handler

    def attach_on_disconnect(self, sid: str, handler: OnDisconnect) -> None:
        self.__on_disconnect_handlers[sid] = handler

    def detach_on_metadata(self, sid: str) -> None:
        if sid in self.__on_metadata_handlers:
            del self.__on_metadata_handlers[sid]

    def detach_on_connect(self, sid: str) -> None:
        if sid in self.__on_connect_handlers:
            del self.__on_connect_handlers[sid]

    def detach_on_disconnect(self, sid: str) -> None:
        if sid in self.__on_disconnect_handlers:
            del self.__on_disconnect_handlers[sid]

    def _get_event(self, sid: str) -> asyncio.Event:
        if sid not in self.__events:
            self.__events[sid] = asyncio.Event()
        return self.__events[sid]

    def _set_event(self, sid: str) -> None:
        self._get_event(sid).set()

    def _del_event(self, sid: str) -> None:
        if sid in self.__events:
            del self.__events[sid]

    async def _on_metadata(self, sid: str, payload: Payload):
        handler = self.__on_metadata_handlers.get(sid)
        if handler:
            await handler(self, sid, payload)

    async def _on_connect(self, sid: str):
        handler = self.__on_connect_handlers.get(sid)
        if handler:
            await handler(self, sid)

    async def _on_disconnect(self, sid: str):
        handler = self.__on_disconnect_handlers.get(sid)
        if handler:
            await handler(self, sid)

    async def _receive_loop(self, web_socket: WebSocket, sid: str):
        serializer = self.get_serializer(sid)
        loads = serializer["loads"]
        dumps = serializer["dumps"]
        event = self._get_event(sid)
        while event.is_set() is False:
            try:
                byte = await web_socket.receive_bytes()
                self.logger.debug(f"WebSocket received {len(byte)} bytes in {sid}")
                payload = Payload.from_bytes(byte, loads)

                await self._on_metadata(sid, payload)
            except WebSocketDisconnect:
                return
            except Exception as e:
                self.logger.error(
                    f"WebSocket ({web_socket.client_state} | {web_socket.application_state}) error in {sid}:\n\t{exc_to_str(e)}"
                )
                # await self.send_bytes(sid, ErrorResponse(error=str(e)).to_bytes(dumps))
                if (
                    web_socket.client_state != WebSocketState.CONNECTED
                    or web_socket.application_state != WebSocketState.CONNECTED
                ):
                    return

    async def _send_loop(self, web_socket: WebSocket, sid: str):
        queue = self.get_send_queue(sid)
        event = self._get_event(sid)
        while event.is_set() is False:
            try:
                data = await queue.get()
                if data is None:
                    return
                await web_socket.send_bytes(data)
            except WebSocketDisconnect:
                return
            except Exception as e:
                self.logger.error(
                    f"WebSocket ({web_socket.client_state} | {web_socket.application_state}) send error in {sid}:\n\t{exc_to_str(e)}"
                )
                if (
                    web_socket.client_state != WebSocketState.CONNECTED
                    or web_socket.application_state != WebSocketState.CONNECTED
                ):
                    return

    async def disconnect(
        self,
        web_socket: WebSocket,
        sid: str | None,
        send_task: asyncio.Task | None,
        receive_task: asyncio.Task | None,
        keep_alive_task: asyncio.Task | None,
    ):
        self.increase_available_connections()
        self.logger.info(f"WebSocket disconnected, remain {self.available_connections}")

        if sid is None:
            return
        if send_task is not None and not send_task.done():
            await self.send_bytes(sid, None)

        self.logger.debug(
            f"WebSocket state in {sid}: {web_socket.client_state} | {web_socket.application_state}"
        )
        if web_socket.client_state == WebSocketState.CONNECTED:
            try:
                # self._set_event(sid)
                await web_socket.close()
            except Exception as e:
                self.logger.error(f"WebSocket close error in {sid}:\n\t{e}")

        tasks = tuple(
            t for t in (send_task, receive_task, keep_alive_task) if t is not None
        )
        for task in tasks:
            if not task.done():
                task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        self._del_event(sid)
        self.detach_on_connect(sid)
        self.detach_on_metadata(sid)
        self.detach_on_disconnect(sid)
        self.del_send_queue(sid)
        self.del_serializer(sid)
        await self._on_disconnect(sid)

    async def connect(
        self,
        web_socket: WebSocket,
        typ: str = MSGPACK,
        keep_alive: bool = False,
        on_metadata: Callable[[Self, str, Payload], Awaitable[None]] | None = None,
        on_connect: Callable[[Self, str], Awaitable[None]] | None = None,
        on_disconnect: Callable[[Self, str], Awaitable[None]] | None = None,
    ) -> None:
        # check connection limit
        if self.available_connections <= 0:
            await web_socket.close()
            self.logger.warning("WebSocket connection limit reached")
            return
        self.decrease_available_connections()
        self.logger.info(f"WebSocket connected, remain {self.available_connections}")

        sid = None
        send_task = None
        receive_task = None
        keep_alive_task = None
        try:
            await web_socket.accept()
            sid = (
                web_socket.headers["sec-websocket-key"]
                if "sec-websocket-key" in web_socket.headers
                else str(uuid.uuid4())
            )

            self.set_serializer(sid, typ)
            send_task = asyncio.create_task(self._send_loop(web_socket, sid))
            receive_task = asyncio.create_task(self._receive_loop(web_socket, sid))
            tasks = [send_task, receive_task]
            if keep_alive:
                keep_alive_task = asyncio.create_task(self._keep_alive_loop(web_socket))
                tasks.append(keep_alive_task)

            if on_metadata is not None:
                self.attach_on_metadata(sid, on_metadata)
            if on_connect is not None:
                self.attach_on_connect(sid, on_connect)
            if on_disconnect is not None:
                self.attach_on_disconnect(sid, on_disconnect)
            await self._on_connect(sid)
            await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        except WebSocketDisconnect:
            return
        except Exception as e:
            raise e
        finally:
            await self.disconnect(
                web_socket, sid, send_task, receive_task, keep_alive_task
            )

    async def _keep_alive_loop(self, web_socket: WebSocket):
        while True:
            try:
                await asyncio.sleep(10)
                await web_socket.send_bytes(b"")
            except WebSocketDisconnect:
                return
            except Exception as e:
                self.logger.error(f"WebSocket keep alive error:\n\t{e}")
                if web_socket.client_state == WebSocketState.DISCONNECTED:
                    return


__all__ = ["Session", "Payload", "FLAGS", "TYPES"]
