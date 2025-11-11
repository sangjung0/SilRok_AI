from dataclasses import field
from typing import Any, Callable
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str
    flag: str = field(default="error")

    def to_bytes(self, dumps_func: Callable[[Any], bytes]) -> bytes:
        payload = dumps_func(self.model_dump())
        return len(payload).to_bytes(4, "big") + payload


__all__ = ["ErrorResponse"]
