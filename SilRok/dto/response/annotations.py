from typing import Annotated
from pydantic import Field


GroupId = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9]{1,255}$",
        min_length=1,
        max_length=255,
        title="group_id",
        description="미팅 고유 ID (숫자·영문, 1-255자)",
        example="Meeting123",
    ),
]

UserId = Annotated[
    str,
    Field(
        # http 요청의 빈 값을 위해
        pattern=r"^[A-Za-z0-9]{0,255}$",
        min_length=0,
        max_length=255,
        title="user_id",
        description="화자 고유 ID (숫자·영문, 1-255자)",
        example="User123",
    ),
]

UserIds = Annotated[
    list[UserId],
    Field(
        title="user_ids",
        description="화자 고유 ID 목록",
        example=["User123", "User456"],
    ),
]

Embedding = Annotated[
    bytes,
    Field(
        min_length=1024,
        max_length=2732,
        description="화자 임베딩 (배열 길이: 512, 바이트 길이: 2048, Base64 인코딩 후 크기: 2732)",
        example="Base64(bytes(embedding))",
    ),
]

Agenda = Annotated[
    list[int],
    Field(
        title="agenda list index",
        description="완료된 아젠다 인덱스를 반환, 0부터 시작",
        example=[0, 1, 2],
    ),
]

Summary = Annotated[
    str,
    Field(
        title="summary",
        max_length=1024 * 8,
        description="LLM이 생성한 대화 요약",
        example="회의 요약 내용",
    ),
]


Feedback = Annotated[
    str,
    Field(
        title="feedback",
        max_length=1024 * 8,
        description="LLM이 생성한 발화자 피드백",
        example="발화자1의 피드백 내용",
    ),
]


__all__ = [
    "GroupId",
    "UserId",
    "Agenda",
    "Summary",
    "Feedback",
    "Embedding",
]
