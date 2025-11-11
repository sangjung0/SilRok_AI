from fastapi import APIRouter, Depends, Response
from dependency_injector.wiring import inject, Provide

from SilRok.containers import Container
from SilRok.dto.request import LIDEmbedRequest, LIDReferenceRequest, LIDRequest
from SilRok.dto.response import LIDEmbedResponse, LIDResponse
from SilRok.usecase import LIDUC

router = APIRouter()


@router.post("/embed_stream", response_model=LIDEmbedResponse)
# @router.post("/embed_stream", response_model=dict)
@inject
async def embed_stream(
    request: LIDEmbedRequest = Depends(LIDEmbedRequest.as_stream),
    uc: LIDUC = Depends(Provide[Container.lid_uc]),
):
    return await uc.embedding(request)


@router.post("/embed_file", response_model=LIDEmbedResponse)
# @router.post("/embed_file", response_model=dict)
@inject
async def embed_file(
    request: LIDEmbedRequest = Depends(LIDEmbedRequest.as_file),
    uc: LIDUC = Depends(Provide[Container.lid_uc]),
):
    return await uc.embedding(request)


@router.post("/refer_stream")
@inject
async def refer(
    request: LIDReferenceRequest = Depends(LIDReferenceRequest.as_stream),
    uc: LIDUC = Depends(Provide[Container.lid_uc]),
):
    await uc.reference(request)
    return Response(status_code=200)


@router.post("/refer_file")
@inject
async def refer_file(
    request: LIDReferenceRequest = Depends(LIDReferenceRequest.as_file),
    uc: LIDUC = Depends(Provide[Container.lid_uc]),
):
    await uc.reference(request)
    return Response(status_code=200)


@router.post("/diarize_stream", response_model=LIDResponse)
@inject
async def stream(
    request: LIDRequest = Depends(LIDRequest.as_stream),
    uc: LIDUC = Depends(Provide[Container.lid_uc]),
):
    return await uc.stream(request)


@router.post("/diarize_file", response_model=LIDResponse)
@inject
async def stream_file(
    request: LIDRequest = Depends(LIDRequest.as_file),
    uc: LIDUC = Depends(Provide[Container.lid_uc]),
):
    return await uc.stream(request)


__all__ = ["router"]
