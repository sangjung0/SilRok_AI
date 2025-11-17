import re

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class LLMOutputTemplate:
    string: str = field(default="")
    ids: list[str] = field(default_factory=list)

    @staticmethod
    def extract_ids_with_template(text: str):
        pattern = re.compile(r"<id>(.*?)</id>", re.DOTALL)
        ids: list[str] = []

        def repl(match: re.Match) -> str:
            ids.append(match.group(1).strip())
            return "%s"

        template = pattern.sub(repl, text)
        return template, ids

    @staticmethod
    def builder(text: str):
        string, ids = LLMOutputTemplate.extract_ids_with_template(text)
        return LLMOutputTemplate(string=string, ids=ids)


@dataclass(slots=True)
class LLMOutput:
    tid: str = field()
    summary: LLMOutputTemplate = field(default_factory=LLMOutputTemplate)
    agenda: list[int] = field(default_factory=list)
    feedback: list[dict[str, str | LLMOutputTemplate]] = field(default_factory=list)

    @staticmethod
    def extract_tagged_summary(response: str) -> LLMOutputTemplate:
        match = re.search(r"<summary>(.*?)</summary>", response, re.DOTALL)
        text = match.group(1).strip() if match else ""
        return LLMOutputTemplate.builder(text)

    @staticmethod
    def extract_tagged_agenda(response: str):
        match = re.search(r"<agenda>(.*?)</agenda>", response, re.DOTALL)
        raw = match.group(1).strip() if match else ""
        return [int(a) for a in raw.split(",")] if raw else []

    @staticmethod
    def extract_tagged_feedback(
        response: str,
    ) -> list[dict[str, str | LLMOutputTemplate]]:
        matches = re.findall(
            r"<feedback name=\"(.*?)\">(.*?)</feedback>", response, re.DOTALL
        )

        feedback = []
        for name, comment in matches:
            feedback.append(
                {
                    "user_id": name.strip(),
                    "comment": LLMOutputTemplate.builder(comment.strip()),
                }
            )

        return feedback

    @staticmethod
    def builder(tid: str, response: str):
        summary = LLMOutput.extract_tagged_summary(response)
        agenda = LLMOutput.extract_tagged_agenda(response)
        feedback = LLMOutput.extract_tagged_feedback(response)
        return LLMOutput(
            tid=tid,
            summary=summary,
            agenda=agenda,
            feedback=feedback,
        )


__all__ = ["LLMOutput", "LLMOutputTemplate"]
