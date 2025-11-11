from fastapi import APIRouter, Depends, WebSocket
from dependency_injector.wiring import inject, Provide

from SilRok.dummy.containers import DummyContainer
from SilRok.ws import Session, TYPES
from SilRok.ws.handlers import LLMHandlerWrapper


router = APIRouter()


@router.websocket("/ws")
@inject
async def websocket(
    ws: WebSocket,
    uc: Session = Depends(Provide[DummyContainer.session]),
    handler: LLMHandlerWrapper = Depends(Provide[DummyContainer.llm_handler_wrapper]),
):
    await uc.connect(
        ws,
        on_metadata=handler.on_metadata,
        on_connect=handler.on_connect,
        on_disconnect=handler.on_disconnect,
    )


@router.websocket("/ws/{type_}")
@inject
async def websocket_type(
    ws: WebSocket,
    type_: str,
    uc: Session = Depends(Provide[DummyContainer.session]),
    handler: LLMHandlerWrapper = Depends(Provide[DummyContainer.llm_handler_wrapper]),
):
    if type_ not in TYPES:
        type_ = TYPES[0]
    await uc.connect(
        ws,
        type_,
        on_metadata=handler.on_metadata,
        on_connect=handler.on_connect,
        on_disconnect=handler.on_disconnect,
    )


__all__ = ["router"]
