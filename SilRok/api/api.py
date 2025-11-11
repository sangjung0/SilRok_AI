from fastapi import APIRouter

from SilRok.api import main, diarization, llm, socket, docs


api_router = APIRouter()
wire_modules = [main, diarization, llm, socket, docs]

api_router.include_router(main.router, prefix="", tags=["Users"])
api_router.include_router(
    diarization.router, prefix="/diarization", tags=["Diarization"]
)
api_router.include_router(llm.router, prefix="/llm", tags=["LLM"])
api_router.include_router(socket.router, prefix="/socket", tags=["Socket"])
api_router.include_router(docs.router, prefix="/docs", tags=["Docs"])

__all__ = ["api_router", "wire_modules"]
