import ray
import asyncio

from collections import defaultdict

from sjpy.collection import LRUDict

from SilRok.services.llm.data import LLMInput, LLMContext, LLMOutput
from SilRok.services.llm.data.flag import UPDATE


@ray.remote(num_cpus=1)
class LLM:
    def __init__(
        self,
        google_cloud_project_id: str,
        google_cloud_location: str,
        google_cloud_service_account_path: str,
        max_storage_size: int,
        max_cache_size: int,
        generative_model_config: dict | None = None,
    ):
        self.gemini = None
        self.logger = None

        self.__locks = None
        self.__storage = None
        self.__GOOGLE_CLOUD_PROJECT_ID = google_cloud_project_id
        self.__GOOGLE_CLOUD_LOCATION = google_cloud_location
        self.__GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH = google_cloud_service_account_path
        self.__MAX_STORAGE_SIZE = max_storage_size
        self.__MAX_CACHE_SIZE = max_cache_size
        self.__GENERATIVE_MODEL_CONFIG = generative_model_config

    def init(self):
        from pathlib import Path
        from sjpy.logger import generate
        from SilRok.services.llm.gemini import Gemini
        from SilRok.core import config

        self.gemini = Gemini(
            self.__GOOGLE_CLOUD_PROJECT_ID,
            self.__GOOGLE_CLOUD_LOCATION,
            self.__GOOGLE_CLOUD_SERVICE_ACCOUNT_PATH,
            self.__GENERATIVE_MODEL_CONFIG,
        )
        self.logger = generate(
            "llm",
            config.service.llm_service.logger.level,
            Path(config.service.llm_service.logger.path),
            config.service.llm_service.logger.file_log_level,
        )

        self.__locks = defaultdict(asyncio.Lock)
        self.__storage = LRUDict(capacity=self.__MAX_STORAGE_SIZE)

        self.logger.info("LLM service initialized")

    def __get_context(self, tid: str) -> LLMContext:
        storage = self.__storage.get(tid)
        if storage is None:
            self.__storage[tid] = LLMContext(tid=tid, model=self.gemini.generate())
        return self.__storage[tid]

    async def request(self, X: LLMInput):
        tid = X.tid
        async with self.__locks[tid]:
            self.logger.debug(f"Received request: {X}")
            context = self.__get_context(tid)
            context.update(X)

            if (
                context.mode == UPDATE
                and len(context.conversation) < self.__MAX_CACHE_SIZE
            ):
                self.logger.debug(f"Updated conversation\n\t{context.conversation}")
                return

            prompt = context.get_prompt()
            self.logger.debug(f"Remembered conversation\n\t{context.conversation}")
            context.conversation = ""

            try:
                response = await context.model.send_message_async(prompt)
                self.logger.debug(f"Prompt: {prompt}")
                self.logger.debug(f"Response: {response.text}")

                return LLMOutput.builder(X.tid, response.text)
            except Exception as e:
                self.logger.error(f"LLM processing error: {e}")
                raise e

    async def close(self):
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        ray.actor.exit_actor()
        self.logger.info("LLM service closed")


__all__ = ["LLM"]
