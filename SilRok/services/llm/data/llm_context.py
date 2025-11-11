from vertexai.generative_models import ChatSession
from dataclasses import dataclass, field

from SilRok.services.llm.data.llm_input import LLMInput
from SilRok.services.llm.data import prompts, flag


@dataclass(slots=True)
class LLMContext:
    tid: str = field()
    model: ChatSession = field(repr=False)

    mode: str = field(default=flag.FEEDBACK)
    agenda: str = field(default="")
    num_people: int = field(default=0)
    meeting_topic: str = field(default="")
    conversation: str = field(default_factory=str)

    def update(self, X: LLMInput):
        if X.tid != self.tid:
            raise ValueError("Context tid does not match")

        self.mode = X.mode
        if X.conversation is not None:
            self.conversation += "\n" + X.conversation
        if X.agenda is not None:
            agenda = ""
            for i, a in enumerate(X.agenda):
                agenda += f"{i+1}. {a}\n"
            self.agenda = X.agenda
        if X.num_people is not None:
            self.num_people = X.num_people
        if X.meeting_topic is not None:
            self.meeting_topic = X.meeting_topic

    def __request(self) -> str:
        # NOTE llm  출력 이상하다면 여기 볼 것
        background = (
            prompts.BACKGROUND.format(
                num_people=self.num_people, meeting_topic=self.meeting_topic
            )
            if self.num_people > 0 and len(self.meeting_topic)
            else ""
        )
        agenda = prompts.AGENDA if self.agenda else ""
        agenda_list = self.agenda
        feedback = prompts.FEEDBACK  # NOTE 피드백 On/Off 있다면,
        conversation = self.conversation

        return prompts.PROMPT.format(
            background=background,
            agenda=agenda,
            feedback=feedback,
            agenda_list=agenda_list,
            conversation=conversation,
        )

    def __update(self) -> str:
        return prompts.JUST_SEND.format(conversation=self.conversation)

    def __done(self) -> str:
        return prompts.FINAL_PROMPT.format(conversation=self.conversation)

    def get_prompt(self) -> str:
        if self.mode == flag.FEEDBACK:
            return self.__request()
        elif self.mode == flag.UPDATE:
            return self.__update()
        elif self.mode == flag.SUMMARY:
            return self.__done()
        else:
            raise ValueError(
                f"Invalid mode: {self.mode}. Must be one of {flag.SUMMARY}, {flag.FEEDBACK}, {flag.UPDATE}."
            )


__all__ = ["LLMContext"]
