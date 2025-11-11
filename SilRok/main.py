import ray
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from SilRok.core import lifespan, config
from SilRok.api import api_router, wire_modules
from SilRok.containers import Container
from SilRok.docs import DESCRIPTION

# dummy
from SilRok.dummy.containers import DummyContainer
from SilRok.dummy.api import test_api_router, test_wire_modules

ray.init(include_dashboard=False)


def server() -> FastAPI:
    manager = Container.get_manager()  # 컨테이너 인스턴스 가져오기
    manager.container.wire(modules=wire_modules)  # 의존성 주입 설정

    test_manager = DummyContainer.get_manager()  # 테스트 컨테이너 인스턴스 가져오기
    test_manager.container.wire(modules=test_wire_modules)  # 테스트 의존성 주입 설정

    # FastAPI 앱 생성
    app = FastAPI(
        title=config.server.name,  # 프로젝트 이름
        version=config.server.version,  # 프로젝트 버전
        description=DESCRIPTION,
        lifespan=lifespan,
    )
    # app.container = container

    # CORS 설정 (프론트엔드 연동할 때 필요)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 모든 도메인 허용 (운영환경에서는 제한 필요)
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록 (API 엔드포인트)
    app.include_router(api_router, prefix="")

    # dummy 라우터 등록 (일단 test로 경로 설정)
    app.include_router(test_api_router, prefix="/test", tags=["Test"])

    return app


# FastAPI 실행 (uvicorn으로 실행하면 필요 없음)
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        server(),
        host="0.0.0.0",
        port=8000,
        ws_ping_interval=30,
        ws_ping_timeout=None,  # 60
        # log_level="debug"
    )
