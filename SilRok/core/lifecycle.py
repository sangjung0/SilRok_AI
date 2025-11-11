from contextlib import asynccontextmanager
from fastapi import FastAPI

from SilRok.core.core import logger
from SilRok.containers import Container
from SilRok.dummy.containers import DummyContainer


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 서버 시작 이벤트
    try:
        await Container.get_manager().start()
        await DummyContainer.get_manager().start()
    except Exception as e:
        raise SystemExit(f"❌ FastAPI 서버 시작 실패: {e}. ")

    # logging.getLogger("uvicorn").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    # logging.getLogger("uvicorn.error").setLevel(logging.WARNING)

    logger.info("🚀 FastAPI 서버 시작!")

    # -------------------------------- #
    yield
    # -------------------------------- #

    # 서버 종료 이벤트
    await Container.get_manager().shutdown_resources()
    await DummyContainer.get_manager().shutdown_resources()

    logger().info("🛑 FastAPI 서버 종료!")


__all__ = ["lifespan"]
