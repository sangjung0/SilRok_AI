from pydantic import BaseModel

from SilRok.dto.request.annotations import (
    AgendaList,
    GroupIdField,
    MeetingTopic,
    NumPeople,
    GroupId,
)
from SilRok.services import LLMInput, llm_mode


class LLMMetadataRequest(BaseModel):
    group_id: GroupIdField
    agenda: AgendaList
    num_people: NumPeople
    meeting_topic: MeetingTopic

    def to_llm_input(self) -> LLMInput:
        return LLMInput(
            tid=self.group_id,
            mode=llm_mode.UPDATE,
            agenda=self.agenda,
            num_people=self.num_people,
            meeting_topic=self.meeting_topic,
        )


class LLMFeedbackRequest(BaseModel):
    group_id: GroupId

    def to_llm_input(self) -> LLMInput:
        return LLMInput(
            tid=self.group_id,
            mode=llm_mode.FEEDBACK,
        )


class LLMSummaryRequest(BaseModel):
    group_id: GroupId

    def to_llm_input(self) -> LLMInput:
        return LLMInput(
            tid=self.group_id,
            mode=llm_mode.SUMMARY,
        )


__all__ = ["LLMMetadataRequest", "LLMFeedbackRequest", "LLMSummaryRequest"]
