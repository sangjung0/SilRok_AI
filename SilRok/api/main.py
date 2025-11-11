from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def read_root():
    return {"message": "Hi, this is the root of the API."}

__all__ = ["router"]
