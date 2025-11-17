from __future__ import annotations
from typing import TYPE_CHECKING

from typing import Any, Callable, TypeVar, Generic
from pydantic import BaseModel, Field

from SilRok.services import LLMOutput
from SilRok.dto.response.annotations import (
    GroupId,
    Summary,
    Agenda,
    Feedback,
    UserId,
    UserIds,
)

if TYPE_CHECKING:
    from SilRok.services import LLMOutputTemplate


T = TypeVar("T")


class StringModel(BaseModel, Generic[T]):
    content: T
    ids: UserIds

    @staticmethod
    def from_llm_output_template(template: LLMOutputTemplate):
        return StringModel(content=template.string, ids=template.ids)


class FeedbackItemModel(BaseModel):
    user_id: UserId
    content: Feedback
    ids: UserIds

    @staticmethod
    def from_feedback_items(items: list[dict[str, LLMOutputTemplate]]):
        return [
            FeedbackItemModel(
                user_id=item["user_id"],
                content=item["comment"].string,
                ids=item["comment"].ids,
            )
            for item in items
        ]


class LLMFeedbackResponse(BaseModel):
    group_id: GroupId
    summary: StringModel[Summary]
    agenda: Agenda
    feedback: list[FeedbackItemModel] = Field(
        default_factory=list,
        min_length=0,
        description="발화자 피드백 목록",
        example=[
            {
                "user_id": "User123",
                "comment": {"string": "피드백 내용", "ids": ["User123"]},
            },
            {
                "user_id": "User456",
                "comment": {"string": "피드백 내용", "ids": ["User456"]},
            },
        ],
    )

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
            summary=StringModel.from_llm_output_template(Y.summary),
            agenda=Y.agenda,
            feedback=FeedbackItemModel.from_feedback_items(Y.feedback),
        )


class LLMSummaryResponse(BaseModel):
    group_id: GroupId
    summary: StringModel[Summary]

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
            summary=StringModel.from_llm_output_template(Y.summary),
        )


__all__ = ["LLMFeedbackResponse", "LLMSummaryResponse"]
