import re

from dataclasses import dataclass, field


@dataclass(slots=True)
class LLMOutput:
    tid: str = field()
    context: str = field(default="")
    agenda: list[int] = field(default_factory=list)
    feedback: list[dict[str, str]] = field(default_factory=list)

    @staticmethod
    def extract_tagged_context(response: str):
        context_match = re.search(r"<context>(.*?)</context>", response, re.DOTALL)
        return context_match.group(1).strip() if context_match else ""

    @staticmethod
    def extract_tagged_agenda(response: str):
        agenda_match = re.search(r"<agenda>(.*?)</agenda>", response, re.DOTALL)
        agenda_raw = agenda_match.group(1).strip() if agenda_match else ""
        return [int(a) for a in agenda_raw.split(",")] if agenda_raw else []

    @staticmethod
    def extract_tagged_feedback(response: str):
        feedback_matches = re.findall(
            r"<correction name=\"(.*?)\">(.*?)</correction>", response, re.DOTALL
        )

        feedback = []
        for name, comment in feedback_matches:
            feedback.append(
                {
                    "user_id": name.strip(),
                    "comment": comment.strip(),
                }
            )

        return feedback

    @staticmethod
    def builder(tid: str, response: str):
        context = LLMOutput.extract_tagged_context(response)
        agenda = LLMOutput.extract_tagged_agenda(response)
        feedback = LLMOutput.extract_tagged_feedback(response)
        return LLMOutput(
            tid=tid,
            context=context,
            agenda=agenda,
            feedback=feedback,
        )


__all__ = ["LLMOutput"]
