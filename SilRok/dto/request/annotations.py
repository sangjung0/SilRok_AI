from typing import Annotated

from fastapi import File, Query
from pydantic import Field


# Query

GroupId = Annotated[
    str,
    Query(
        pattern=r"^[A-Za-z0-9]{1,255}$",
        min_length=1,
        max_length=255,
        title="group_id",
        description="미팅 고유 ID (숫자·영문, 1-255자)",
        examples={
            "default": {"summary": "기본 예시", "value": "Meeting123"},
            "numeric": {"summary": "숫자 ID", "value": "20240522"},
        },
    ),
]

UserId = Annotated[
    str,
    Query(
        pattern=r"^[A-Za-z0-9]{1,255}$",
        min_length=1,
        max_length=255,
        title="user_id",
        description="화자 고유 ID (숫자·영문, 1-255자)",
        examples={
            "default": {"summary": "기본 유저 ID", "value": "User123"},
            "anon": {"summary": "익명 사용자", "value": "Speaker007"},
        },
    ),
]

Offset = Annotated[
    int | None,
    Query(
        title="offset",
        description="음성 시작 오프셋 sample rate 단위. 모델은 1초에 16000 샘플을 사용하므로, 1초는 16000, 0.5초는 8000, 0.25초는 4000",
        examples={
            "default": {
                "summary": "기본 오프셋",
                "value": 0,
            },
            "half_second": {
                "summary": "0.5초 오프셋",
                "value": 8000,
            },
        },
    ),
]

SampleRate = Annotated[
    int,
    Query(
        title="sample_rate",
        description=f"전달하는 샘플링 주파수 (Hz)",
        examples={
            "default": {
                "summary": "기본 샘플레이트",
                "value": 16000,
            },
            "high": {"summary": "높은 샘플레이트", "value": 48000},
        },
    ),
]

Language = Annotated[
    str | None,
    Query(
        title="language",
        description="음성 언어 코드 (예: 'en' 영어, 'ko' 한국어). 지정하지 않으면 자동 감지",
        excamples={
            "default": {"summary": "자동 감지", "value": None},
            "korean": {"summary": "한국어", "value": "ko"},
            "english": {"summary": "영어", "value": "en"},
            "japanese": {"summary": "일본어", "value": "ja"},
            "chinese": {"summary": "중국어", "value": "zh"},
        },
    ),
]

Agenda = Annotated[
    str,
    Query(
        title="agenda",
        description="아젠다 (1-1024자)",
        min_length=1,
        max_length=1024,
        examples={
            "basic": {"summary": "일반 주제", "value": "웹 소켓 통신 방법에 대해 논의"},
            "detailed": {
                "summary": "구체적 논의",
                "value": "AI 기반 실시간 회의 요약 기능 개선",
            },
        },
    ),
]

AgendaList = Annotated[
    list[str] | None,  # list[Agenda] | None
    Query(
        default=None,
        title="agenda_list",
        description="아젠다 리스트, 최대 255, 번호는 자동으로 붙여주므로, 번호는 붙이지 말 것",
        min_length=1,
        max_length=255,
        examples={
            "basic": {
                "summary": "간단한 예시",
                "value": ["웹 소켓 통신 방법에 대해 논의", "AI 모델 개선 방향 논의"],
            },
        },
    ),
]

NumPeople = Annotated[
    int | None,
    Query(
        default=None,
        title="num_people",
        description="회의 참석자 수 (1-100)",
        ge=1,
        le=100,
        examples={
            "small": {"summary": "소규모", "value": 4},
            "large": {"summary": "대규모", "value": 30},
        },
    ),
]

MeetingTopic = Annotated[
    str | None,
    Query(
        default=None,
        title="meeting_topic",
        description="회의 주제 (1-4096자)",
        min_length=1,
        max_length=4096,
        examples={
            "short": {"summary": "간단 주제", "value": "웹 소켓 통신 논의"},
            "long": {
                "summary": "상세 주제",
                "value": "AI 음성 인식 기반 회의 분석 시스템 개발",
            },
        },
    ),
]

UserIds = Annotated[
    list[str],
    Query(
        min_length=1,
        max_length=255,
        title="user_ids",
        description="화자 고유 ID 리스트 (최대 255개)",
        examples={
            "default": {
                "summary": "기본 화자 ID 리스트",
                "value": ["User123", "User456", "User789"],
            },
        },
    ),
]

Counts = Annotated[
    list[int],
    Query(
        min_length=1,
        max_length=255,
        title="counts",
        description="화자별 임베딩 개수 리스트 (최대 255개)",
        examples={
            "default": {
                "summary": "기본 임베딩 개수 리스트",
                "value": [3, 2, 4],
            },
        },
    ),
]


# File
AudioFile = Annotated[
    bytes,
    File(
        title="audio",
        description="wav 음성 파일을 opus로 압축한 후 base64로 인코딩한 값",
        example="base64(opus(wav))",
    ),
]

RefersFile = Annotated[
    bytes,
    File(
        title="embed",
        description="wav 음성 파일을 opus로 압축한 후 base64로 인코딩한 값, 임베딩 생성에 사용",
        example="opus(wav)",
    ),
]

# Field

GroupIdField = Annotated[
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

UserIdField = Annotated[
    str,
    Field(
        pattern=r"^[A-Za-z0-9]{1,255}$",
        min_length=1,
        max_length=255,
        title="user_id",
        description="화자 고유 ID (숫자·영문, 1-255자)",
        example="User123",
    ),
]

EmbeddingField = Annotated[
    str,
    Field(
        min_length=2700,
        max_length=2750,
        description="화자 임베딩 (배열 길이: 512, 바이트 길이: 2048, Base64 인코딩 후 크기: 2732)",
        example="Base64(bytes(embedding))",
    ),
]

__all__ = [
    "GroupId",
    "UserId",
    "Offset",
    "Language",
    "Agenda",
    "AgendaList",
    "NumPeople",
    "MeetingTopic",
    "UserIds",
    "Counts",
    "AudioFile",
    "RefersFile",
    "GroupIdField",
    "UserIdField",
    "EmbeddingField",
    "SampleRate",
]
