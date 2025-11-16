from functools import lru_cache
from dependency_injector import providers
from dependency_injector.containers import DeclarativeContainer

from sjpy.collection import namespace_to_dict

from SilRok.core import config_dict, logger
from SilRok.services import LLMService, LIDService
from SilRok.usecase import LLMUC, LIDUC
from SilRok.ws import Session
from SilRok.ws.handlers import LLMHandlerWrapper
from SilRok.containers.container_manager import ContainerManager


class Container(DeclarativeContainer):
    manager: ContainerManager = None
    config = providers.Configuration()
    logger = logger

    # service
    llm_service = providers.Resource(
        LLMService,
        logger=logger,
        google_cloud_project_id=config.service.llm_service.google_cloud_project_id,
        google_cloud_location=config.service.llm_service.google_cloud_location,
        google_cloud_service_account_path=config.service.llm_service.google_cloud_service_account_path,
        max_storage_size=config.service.llm_service.max_storage_size,
        max_cache_size=config.service.llm_service.max_cache_size,
    )

    lid_service = providers.Resource(
        LIDService,
        logger=logger,
        diarizer_job_num=config.service.lid_service.diarizer_job_num,
        asr_job_num=config.service.lid_service.asr_job_num,
        minimum_chunk_duration=config.service.lid_service.minimum_chunk_duration,
        inactive_sec=config.service.lid_service.inactive_sec,
        broker_options=namespace_to_dict(config.service.lid_service.broker_options),
        diarizer_options=namespace_to_dict(config.service.lid_service.diarizer_options),
        asr_options=namespace_to_dict(config.service.lid_service.asr_options),
    )

    # usecase
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

    # socket
    session = providers.Singleton(
        Session,
        logger=logger,
        max_connection=config.service.session.max_connection,
        max_send_queue_size=config.service.session.max_send_queue_size,
    )

    # socket handlers
    llm_handler_wrapper = providers.Singleton(
        LLMHandlerWrapper,
        llm_service=llm_service,
        logger=logger,
        lid_service=lid_service,
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        if Container.manager is not None:
            raise Exception(
                f"MainContainer is a singleton class. Use MainContainer.get_manager() instead."
            )

    @lru_cache(maxsize=1)
    @staticmethod
    def get_manager(*args, **kwargs):
        if Container.manager is None:
            container = Container(*args, **kwargs)
            container.config.update(config_dict)
            Container.manager = ContainerManager(container)
        return Container.manager


__all__ = ["Container"]
