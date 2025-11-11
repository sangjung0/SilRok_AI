import base64

from typing import Any, Callable
from pydantic import BaseModel
from pydantic import Field

from LID.asr.data import Word as LIDWord
from LID.broker.data import SpeakerSentence

from SilRok.services import LIDSentence, Embedding as EmbedOutput
from SilRok.dto.response.annotations import Embedding, UserId


class Word(BaseModel):
    start: int
    end: int
    text: str
    lang: str

    @staticmethod
    def from_lid_word(word: LIDWord):
        return Word(start=word.start, end=word.end, text=word.text, lang=word.language)


class Sentence(BaseModel):
    order: int
    lang: list[str]
    text: str
    words: list[Word]
    user_id: str = Field(default=None)
    audio_id: str = Field(default=None)

    @staticmethod
    def from_speaker_sentence(sentence: SpeakerSentence):
        return Sentence(
            order=sentence.order,
            lang=sentence.language,
            text=sentence.text,
            words=[Word.from_lid_word(word) for word in sentence.words],
            user_id=sentence.speaker,
            audio_id=sentence.source_id,
        )


class LIDResponse(BaseModel):
    group_id: str
    completed: list[Sentence]
    candidate: list[Sentence]

    # NOTE front 요청으로 임의 설정
    flag: str = "diarized"

    def to_bytes(self, dump_func: Callable[[Any], bytes]):
        bt = dump_func(self.model_dump())
        return len(bt).to_bytes(4, "big") + bt

    @staticmethod
    def from_lid_sentence(Y: LIDSentence):
        return LIDResponse(
            group_id=Y.gid,
            completed=[Sentence.from_speaker_sentence(speak) for speak in Y.completed],
            candidate=[Sentence.from_speaker_sentence(speak) for speak in Y.candidate],
        )


class LIDEmbedResponse(BaseModel):
    user_id: UserId
    embedding: Embedding

    # NOTE front 요청으로 임의 설정
    flag: str = "embedded"

    def to_bytes(self, dump_func: Callable[[Any], bytes]):
        bt = dump_func(self.model_dump(exclude={"embedding"}))
        return len(bt).to_bytes(4, "big") + bt + self.embedding

    # NOTE Http Response를 위해 임시로 조치
    def to_dict(self):
        return {
            "user_id": self.user_id,
            "embedding": base64.b64encode(self.embedding).decode("utf-8"),
            "flag": self.flag,
        }

    @staticmethod
    def from_embedding(embedding: EmbedOutput) -> "LIDEmbedResponse":
        b = embedding.embedding.reshape(-1).tobytes()
        return LIDEmbedResponse(user_id=embedding.uid, embedding=b)


__all__ = ["LIDResponse"]
