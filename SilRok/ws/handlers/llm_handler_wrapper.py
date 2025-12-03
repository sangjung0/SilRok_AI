from typing import Awaitable, Callable, Any
from typing_extensions import override

from dataclasses import dataclass
from functools import cached_property

from SilRok.services import LLMInput, LLMOutput, LLMService, LIDSentence, llm_mode
from SilRok.ws.session import Payload, Session, FLAGS
from SilRok.ws.handlers.lid_handler import LIDHandler

LLM_METADATA = "metadata"
LLM_FEEDBACK = "context"
LLM_SUMMARY = "context_done"
LLM_FLAGS = set(
    [
        LLM_METADATA,
        LLM_FEEDBACK,
        LLM_SUMMARY,
    ]
)


@dataclass(frozen=True)
class LLMPayload:
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
    def agenda(self):
        return self.payload.metadata.get("agenda", None)

    @cached_property
    def num_people(self):
        return self.payload.metadata.get("num_people", None)

    @cached_property
    def meeting_topic(self):
        return self.payload.metadata.get("meeting_topic", None)

    def to_llm_metadata(self) -> LLMInput:
        return LLMInput(
            tid=self.gid,
            mode=llm_mode.UPDATE,
            agenda=self.agenda,
            num_people=self.num_people,
            meeting_topic=self.meeting_topic,
        )

    def to_llm_feedback(self) -> LLMInput:
        return LLMInput(
            tid=self.gid,
            mode=llm_mode.FEEDBACK,
        )

    def to_llm_summary(self) -> LLMInput:
        return LLMInput(
            tid=self.gid,
            mode=llm_mode.SUMMARY,
        )

    @staticmethod
    def from_payload(payload: Payload):
        return LLMPayload(payload=payload)


class LLMHandlerWrapper(LIDHandler):
    def __init__(self, llm_service: LLMService, *args, **kwargs):
        for flag in LLM_FLAGS:
            FLAGS.add(flag)

        super().__init__(*args, **kwargs)
        self.llm_service = llm_service

    @override
    async def on_connect(self, session: Session, sid: str):
        send, callbacks = await super().on_connect(session, sid)

        dumps = session.get_serializer(sid)["dumps"]
        summary_callback = self._llm_summary_callback(send, dumps)
        feedback_callback = self._llm_feedback_callback(send, dumps)

        callbacks[LLM_METADATA] = feedback_callback
        callbacks[LLM_FEEDBACK] = feedback_callback
        callbacks[LLM_SUMMARY] = summary_callback

        return send, callbacks

    @override
    async def on_metadata(self, session: Session, sid: str, payload: Payload) -> bool:
        if await super().on_metadata(session, sid, payload):
            return True
        flag = payload.flag
        if flag not in LLM_FLAGS:
            return False

        lp = LLMPayload.from_payload(payload)
        if flag == LLM_METADATA:
            callback = self.get_callbacks(sid)[LLM_METADATA]
            self.llm_service.request_with_callback(lp.to_llm_metadata(), callback)
            self.logger.debug(f"{sid}: llm register metadata")
        elif flag == LLM_FEEDBACK:
            callback = self.get_callbacks(sid)[LLM_FEEDBACK]
            self.llm_service.request_with_callback(lp.to_llm_feedback(), callback)
            self.logger.debug(f"{sid}: llm register feedback")
        elif flag == LLM_SUMMARY:
            callback = self.get_callbacks(sid)[LLM_SUMMARY]
            self.llm_service.request_with_callback(lp.to_llm_summary(), callback)
            self.logger.debug(f"{sid}: llm register summary")
        return True

    @override
    def _lid_stream_callback(
        self, send: Callable[[bytes], Awaitable[None]], dumps: Callable[[Any], bytes]
    ):
        dsp = super()._lid_stream_callback(send, dumps)

        async def dummy(*args, **kwargs):
            return None

        async def callback(Y: LIDSentence | None, e: Exception | None):
            if Y is not None and Y.completed:
                self.llm_service.request_with_callback(
                    LLMInput(
                        tid=Y.gid,
                        mode=llm_mode.UPDATE,
                        conversation="\n".join(
                            f"{s.speaker}: {s.text}" for s in Y.completed
                        ),
                    ),
                    dummy,
                )
            await dsp(Y, e)

        return callback

    def _llm_summary_callback(
        self, send: Callable[[bytes], Awaitable[None]], dumps: Callable[[Any], bytes]
    ):
        from SilRok.dto.response import ErrorResponse, LLMSummaryResponse

        async def callback(Y: LLMOutput | None, e: Exception | None):
            if Y is not None:
                self.logger.debug(f"LLM Summary Output: {Y}")
                await send(LLMSummaryResponse.from_llm_output(Y).to_bytes(dumps))
            if e is not None:
                self.logger.error(f"Error in llm summary callback:\n\t{e}")
                # await send(ErrorResponse(error=str(e)).to_bytes(dumps))

        return callback

    def _llm_feedback_callback(
        self, send: Callable[[bytes], Awaitable[None]], dumps: Callable[[Any], bytes]
    ):
        from SilRok.dto.response import ErrorResponse, LLMFeedbackResponse

        async def callback(Y: LLMOutput | None, e: Exception | None):
            if Y is not None:
                self.logger.debug(f"LLM Feedback Output: {Y}")
                await send(LLMFeedbackResponse.from_llm_output(Y).to_bytes(dumps))
            if e is not None:
                self.logger.error(f"Error in llm feedback callback:\n\t{e}")
                # await send(ErrorResponse(error=str(e)).to_bytes(dumps))

        return callback


__all__ = ["LLMHandlerWrapper"]
