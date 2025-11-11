from fastapi import Depends, Response
from fastapi.routing import APIRouter
from dependency_injector.wiring import inject, Provide

from SilRok.dummy.containers import DummyContainer
from SilRok.dto.request import LLMMetadataRequest, LLMFeedbackRequest, LLMSummaryRequest
from SilRok.dto.response import LLMSummaryResponse, LLMFeedbackResponse
from SilRok.usecase import LLMUC


router = APIRouter()


@router.get("/metadata")
@inject
async def metadata(
    request: LLMMetadataRequest = Depends(),
    uc: LLMUC = Depends(Provide[DummyContainer.llm_uc]),
):
    await uc.metadata(request)
    return Response(status_code=200)


@router.get("/context", response_model=LLMFeedbackResponse)
@inject
async def context(
    request: LLMFeedbackRequest = Depends(),
    uc: LLMUC = Depends(Provide[DummyContainer.llm_uc]),
):
    return await uc.context(request)


@router.get("/context_done", response_model=LLMSummaryResponse)
@inject
async def context_done(
    request: LLMSummaryRequest = Depends(),
    uc: LLMUC = Depends(Provide[DummyContainer.llm_uc]),
):
    return await uc.context_done(request)


__all__ = ["router"]
