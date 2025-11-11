from typing import Any, Callable
from pydantic import BaseModel

from SilRok.dto.response.annotations import GroupId, Context, Agenda, Feedback
from SilRok.services import LLMOutput


class LLMFeedbackResponse(BaseModel):
    group_id: GroupId
    context: Context
    agenda: Agenda
    feedback: Feedback

    # NOTE front 요청으로 임의 설정
    flag: str = "context"
    is_recap: bool = True

    def to_bytes(self, dump_func: Callable[[Any], bytes]):
        bt = dump_func(self.model_dump())
        return len(bt).to_bytes(4, "big") + bt

    @staticmethod
    def from_llm_output(Y: LLMOutput):
        return LLMFeedbackResponse(
            group_id=Y.tid,
            context=Y.context,
            agenda=Y.agenda,
            feedback=Y.feedback,
        )


class LLMSummaryResponse(BaseModel):
    group_id: GroupId
    context: Context

    # NOTE front 요청으로 임의 설정
    flag: str = "context"
    is_recap: bool = False

    def to_bytes(self, dump_func: Callable[[Any], bytes]):
        bt = dump_func(self.model_dump())
        return len(bt).to_bytes(4, "big") + bt

    @staticmethod
    def from_llm_output(Y: LLMOutput):
        return LLMSummaryResponse(
            group_id=Y.tid,
            context=Y.context,
        )


__all__ = ["LLMFeedbackResponse", "LLMSummaryResponse"]
