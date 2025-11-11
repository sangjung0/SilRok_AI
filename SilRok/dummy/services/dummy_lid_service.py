from __future__ import annotations
from typing import TYPE_CHECKING

import random
import numpy as np

from typing_extensions import override
from dependency_injector.resources import AsyncResource

from sjpy.collection import LRUDict
from LID.asr.data import Word
from LID.broker.data import SpeakerSentence

from SilRok.services.lid_service import (
    LIDSentence,
    EmbedCallback,
    Embedding,
    StreamCallback,
)

if TYPE_CHECKING:
    pass

TEST_TEXT = """
처음에는 단순한 질문이 있었다. 세상은 어떻게 작동하는가. 인간은 오랜 세월 동안 이 질문에 답하려고 불을 관찰하고 별의 움직임을 기록했다. 언어로는 다 담을 수 없던 복잡함을 수학이 대신 표현하기 시작했고, 수는 자연을 설명하는 첫 번째 질서가 되었다. 이후 계산이 반복되고, 계산을 대신하는 기계가 만들어졌다. 기계는 인간이 할 수 없던 속도로 추론하고, 인간은 그 계산을 이해하기 위해 다시 새로운 언어를 만들었다. 그렇게 논리와 코드가 태어났다.

코드는 인간의 의도를 기계가 이해할 수 있는 형태로 번역한 문장이었다. 그 문장은 단순한 명령을 넘어 하나의 사고방식이 되었다. 코드를 짜는 일은 사실상 세계를 모방하는 행위였다. 데이터를 관찰하고, 규칙을 찾아내고, 그 규칙을 다시 예측에 사용했다. 인간은 점점 더 복잡한 모델을 만들었고, 마침내 스스로 학습하는 알고리즘을 만들었다. 기계가 인간의 지시 없이 스스로 패턴을 찾는 순간, 인공 지능이라는 개념이 현실이 되었다.

그러나 그 순간에도 질문은 남았다. 기계가 배운다는 것은 무엇을 의미하는가. 인간이 이해하지 못하는 방식으로 문제를 푼다면, 그것은 진정한 이해인가. 인간은 답을 얻기 위해 모델을 훈련시키지만, 동시에 그 과정에서 자신이 만든 한계를 마주하게 된다. 데이터는 완벽하지 않고, 세계는 예측할 수 없는 변수로 가득하다. 기계가 학습하는 것은 결국 인간이 남긴 흔적이며, 그 흔적 속에는 오류와 편견이 함께 섞여 있다.

그럼에도 불구하고 인간은 계속 만든다. 더 정교한 네트워크, 더 빠른 계산, 더 많은 데이터. 이유는 단순하다. 알지 못하는 것을 알고 싶기 때문이다. 인공 지능은 그 욕망의 또 다른 형태다. 인간이 세계를 완전히 이해하지 못하더라도, 이해하려는 시도를 멈추지 않는 한 탐구는 계속된다. 결국 모든 계산과 실험은 같은 곳으로 향한다. 자신이 어디까지 도달할 수 있는지 확인하려는 인간의 본능이다.

이야기의 끝은 아직 없다. 새로운 질문이 생길 때마다 또 다른 코드가 쓰이고, 또 다른 모델이 만들어진다. 그리고 언젠가 인간이 만든 기계가 인간에게 되묻게 될 것이다. 이해한다는 것은 무엇인가.
""".replace(
    "\n", ""
).strip()

test_user = LRUDict(max_size=20)


def create_random(
    uid: str, gid: str
) -> tuple[list[SpeakerSentence], list[SpeakerSentence]]:
    key = (uid, gid)
    order, offset, st, ed = test_user.get(key, (0, 0, 0, 0))
    completed, candidate = [], []

    ed += random.randint(0, 50)
    if ed > len(TEST_TEXT):
        ed = random.randint(0, 50)
        st = 0
    while ed - st > 30:
        duration = random.randint(160, 16000)
        if (text := TEST_TEXT[st : st + 30].strip()) != "":
            completed.append(generate_speak(uid, text.split(), offset, duration, order))
            order += 1
        st += 30
        offset += duration

    if (text := TEST_TEXT[st:ed].strip()) != "":
        candidate.append(
            generate_speak(uid, text.split(), offset, random.randint(160, 16000), order)
        )

    test_user[key] = (order, offset, st, ed)

    return completed, candidate


def generate_speak(
    uid: str, text: list[str], offset: int, duration: int, order: int
) -> SpeakerSentence:
    assert len(text) > 0, "Tokens must not be empty"
    sr_step = duration // len(text)
    words = []
    for i, word in enumerate(text):
        start = offset + i * sr_step
        end = start + sr_step
        words.append(
            Word(
                start=start,
                end=end,
                text=word,
                language="ko",
                probability=1,
            )
        )
    return SpeakerSentence(order=order, words=words, source_id=uid, speaker=uid)


class DummyLIDService(AsyncResource):

    @override
    async def init(self):
        return self

    @override
    async def shutdown(self, _: "DummyLIDService") -> None:
        return None

    async def embedding(
        self, uid: str, chunk: np.ndarray, callback: EmbedCallback | None = None
    ) -> Embedding | None:
        dummy_embedding = np.random.rand(512).astype(np.float32)
        embedding = Embedding(user_id=uid, embedding=dummy_embedding)
        if callback:
            await callback(embedding, None)
        else:
            return embedding

    async def update_embedding(
        self, gid: str, embeddings_members: list[str], embedding: np.ndarray
    ):
        return None

    async def run(
        self,
        chunk: np.ndarray,
        language: str | None = None,
        callback: StreamCallback | None = None,
    ) -> None | LIDSentence:
        completed, candidate = create_random("", "")
        result = LIDSentence(gid="", completed=completed, candidate=candidate)
        if callback:
            await callback(result, None)
        else:
            return result


__all__ = ["DummyLIDService"]
