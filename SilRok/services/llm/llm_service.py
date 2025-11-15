import asyncio

from logging import Logger
from typing import Callable
from typing_extensions import Self, override
from dependency_injector.resources import AsyncResource

from sjpy.asynchronous import spawn_task_with_callback

from SilRok.services.llm.llm import LLM
from SilRok.services.llm.data import LLMInput, LLMOutput


class LLMService(AsyncResource):
    def __init__(
        self,
        logger: Logger,
        google_cloud_project_id: str,
        google_cloud_location: str,
        google_cloud_service_account_path: str,
        max_storage_size: int,
        max_cache_size: int,
        generative_model_config: dict | None = None,
    ):
        super().__init__()
        if not isinstance(logger, Logger):
            raise TypeError("logger must be an instance of logging.Logger")
        if not isinstance(max_storage_size, int) or max_storage_size <= 0:
            raise ValueError("max_storage_size must be a positive integer")
        if not isinstance(max_cache_size, int) or max_cache_size <= 0:
            raise ValueError("max_cache_size must be a positive integer")

        self.logger = logger
        self.llm: LLM = LLM.remote(
            google_cloud_project_id,
            google_cloud_location,
            google_cloud_service_account_path,
            max_storage_size,
            max_cache_size,
            generative_model_config,
        )

    @override
    async def init(self, *_, **__) -> Self:
        await self.llm.init.remote()

        self.logger.info("LLM service initialized")
        return self

    @override
    async def shutdown(self, _: Self) -> None:
        await self.llm.close.remote()
        self.logger.info("LLM service closed")

    def request_with_callback(
        self,
        X: LLMInput,
        callback: Callable[[LLMOutput | None, Exception | None], None],
    ) -> None:
        spawn_task_with_callback(self.request(X), callback, self.logger)

    async def request(self, X: LLMInput) -> LLMOutput | None:
        assert isinstance(X, LLMInput), "X must be an instance of LLMInput"

        result = await self.llm.request.remote(X)

        assert (
            isinstance(result, LLMOutput) or result is None
        ), "result must be an instance of LLMOutput or None"

        return result


__all__ = ["LLMService"]
