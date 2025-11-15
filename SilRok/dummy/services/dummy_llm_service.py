from __future__ import annotations
from typing import TYPE_CHECKING

import asyncio
import random

from typing import Callable, Awaitable
from typing_extensions import override
from dataclasses import dataclass
from dependency_injector.resources import AsyncResource

from sjpy.asynchronous import spawn_task_with_callback

from SilRok.services import LLMInput, LLMOutput

if TYPE_CHECKING:
    pass


@dataclass(slots=True)
class DummyLLMOutput(LLMOutput):
    @staticmethod
    def create_random(X: LLMInput) -> "DummyLLMOutput":
        agenda_len = len(X.agenda) if X.agenda else 0
        tid = X.tid
        context = f"This is a test context for group {tid}."
        agenda = random.sample(range(agenda_len), random.randint(0, agenda_len))
        feedback = [
            {"user_id": f"user_{i}", "comment": f"This is a test comment {i}"}
            for i in random.sample(range(1, 6), random.randint(0, 3))
        ]
        return DummyLLMOutput(
            tid=tid,
            context=context,
            agenda=agenda,
            feedback=feedback,
        )


class DummyLLMService(AsyncResource):
    @override
    async def init(self):
        return self

    @override
    async def shutdown(self, _: "DummyLLMService") -> None:
        return None

    def request_with_callback(
        self,
        X: LLMInput,
        callback: Callable[[LLMOutput | None, Exception | None], Awaitable],
    ) -> None:
        spawn_task_with_callback(self.request(X), callback)

    async def request(self, X: LLMInput) -> LLMOutput | None:
        return DummyLLMOutput.create_random(X)


__all__ = ["DummyLLMService"]
