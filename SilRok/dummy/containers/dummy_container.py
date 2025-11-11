from functools import lru_cache
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from SilRok.core import config_dict, logger
from SilRok.usecase import LLMUC, LIDUC
from SilRok.ws import Session
from SilRok.ws.handlers import LLMHandlerWrapper
from SilRok.dummy.services import DummyLIDService, DummyLLMService
from SilRok.containers.container_manager import ContainerManager


class DummyContainer(DeclarativeContainer):
    manager: ContainerManager = None
    config = providers.Configuration()
    logger = logger

    # dummy - service
    lid_service = providers.Resource(DummyLIDService)
    llm_service = providers.Resource(DummyLLMService)

    # dummy - usecase
    lid_uc = providers.Singleton(
        LIDUC,
        lid_service=lid_service,
        llm_service=llm_service,
        sample_rate=config.service.common.sample_rate,
        embedding_length=config.service.common.embedding_length,
    )

    llm_uc = providers.Singleton(
        LLMUC,
        llm_service=llm_service,
    )

    # dummy - socket
    session = providers.Singleton(
        Session,
        logger=logger,
        max_connection=config.service.session.max_connection,
        max_send_queue_size=config.service.session.max_send_queue_size,
    )

    # dummy handlers
    llm_handler_wrapper = providers.Singleton(
        LLMHandlerWrapper,
        llm_service=llm_service,
        logger=logger,
        lid_service=lid_service,
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if DummyContainer.manager is not None:
            raise Exception(
                f"MainContainer is a singleton class. Use MainContainer.get_manager() instead."
            )

    @lru_cache(maxsize=1)
    @staticmethod
    def get_manager(*args, **kwargs):
        if DummyContainer.manager is None:
            container = DummyContainer(*args, **kwargs)
            container.config.update(config_dict)
            DummyContainer.manager = ContainerManager(container)
        return DummyContainer.manager


__all__ = ["DummyContainer"]
