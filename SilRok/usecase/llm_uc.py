from SilRok.dto.request import LLMSummaryRequest, LLMMetadataRequest, LLMFeedbackRequest
from SilRok.dto.response import LLMSummaryResponse, LLMFeedbackResponse
from SilRok.services import LLMInput, LLMService, llm_mode


class LLMUC:
    def __init__(self, llm_service: LLMService):
        super().__init__()
        self.llm_service = llm_service

    async def metadata(self, llm_metadata_request: LLMMetadataRequest) -> None:
        await self.llm_service.request(
            LLMInput(
                tid=llm_metadata_request.group_id,
                mode=llm_mode.UPDATE,
                agenda=llm_metadata_request.agenda,
                num_people=llm_metadata_request.num_people,
                meeting_topic=llm_metadata_request.meeting_topic,
            )
        )

    async def feedback(
        self, llm_feedback_request: LLMFeedbackRequest
    ) -> LLMFeedbackResponse:
        return LLMFeedbackResponse.from_llm_output(
            await self.llm_service.request(
                LLMInput(tid=llm_feedback_request.group_id, mode=llm_mode.FEEDBACK)
            )
        )

    async def summary(
        self, llm_summary_request: LLMSummaryRequest
    ) -> LLMSummaryResponse:
        return LLMSummaryResponse.from_llm_output(
            await self.llm_service.request(
                LLMInput(tid=llm_summary_request.group_id, mode=llm_mode.SUMMARY)
            )
        )


__all__ = ["LLMUC"]
