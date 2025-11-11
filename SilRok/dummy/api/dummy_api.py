from fastapi import APIRouter

from SilRok.dummy.api import dummy_diarization, dummy_llm, dummy_main, dummy_socket


test_api_router = APIRouter()
test_wire_modules = [dummy_main, dummy_diarization, dummy_llm, dummy_socket]

test_api_router.include_router(dummy_main.router, prefix="", tags=["Users"])
test_api_router.include_router(
    dummy_diarization.router, prefix="/diarization", tags=["Diarization"]
)
test_api_router.include_router(dummy_llm.router, prefix="/llm", tags=["LLM"])
test_api_router.include_router(dummy_socket.router, prefix="/socket", tags=["Socket"])

__all__ = ["test_api_router", "test_wire_modules"]
