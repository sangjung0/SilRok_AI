from typing_extensions import override
from dataclasses import dataclass, field

from SilRok.services.llm.data import flag


@dataclass(slots=True)
class LLMInput:
    tid: str = field()
    mode: str = field(default=flag.FEEDBACK)
    conversation: str | None = field(default=None)
    agenda: list[str] | None = field(default=None)
    num_people: int | None = field(default=None)
    meeting_topic: str | None = field(default=None)

    @override
    def __post_init__(self):
        if self.mode not in [flag.SUMMARY, flag.FEEDBACK, flag.UPDATE]:
            raise ValueError(
                f"Invalid mode: {self.mode}. Must be one of {flag.SUMMARY}, {flag.FEEDBACK}, {flag.UPDATE}."
            )


__all__ = ["LLMInput"]
