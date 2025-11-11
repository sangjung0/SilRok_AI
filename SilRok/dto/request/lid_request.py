from fastapi import Request
from pydantic import BaseModel

from SilRok.dto.request.annotations import (
    AudioFile,
    GroupId,
    UserId,
    Counts,
    RefersFile,
    UserIds,
    Offset,
    Language,
    SampleRate,
)


class LIDEmbedRequest(BaseModel):
    audio: bytes
    sample_rate: SampleRate

    @classmethod
    async def as_file(cls, audio: AudioFile, sample_rate: SampleRate = 16000):
        return cls(audio=audio, sample_rate=sample_rate)

    @classmethod
    async def as_stream(cls, audio: Request, sample_rate: SampleRate = 16000):
        return cls(audio=await audio.body(), sample_rate=sample_rate)


class LIDReferenceRequest(BaseModel):
    group_id: GroupId
    user_id: UserId
    user_ids: UserIds
    counts: Counts
    refers: RefersFile

    @classmethod
    async def as_file(
        cls,
        group_id: GroupId,
        user_id: UserId,
        user_ids: UserIds,
        counts: Counts,
        refers: RefersFile,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            user_ids=user_ids,
            counts=counts,
            refers=refers,
        )

    @classmethod
    async def as_stream(
        cls,
        group_id: GroupId,
        user_id: UserId,
        user_ids: UserIds,
        counts: Counts,
        refers: Request,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            user_ids=user_ids,
            counts=counts,
            refers=await refers.body(),
        )


class LIDRequest(BaseModel):
    group_id: GroupId
    user_id: UserId
    sc_offset: Offset
    audio: bytes
    sample_rate: SampleRate
    language: Language

    @classmethod
    async def as_file(
        cls,
        group_id: GroupId,
        user_id: UserId,
        audio: AudioFile,
        sc_offset: Offset = None,
        sample_rate: SampleRate = 16000,
        language: Language = None,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            sc_offset=sc_offset,
            audio=audio,
            sample_rate=sample_rate,
            language=language,
        )

    @classmethod
    async def as_stream(
        cls,
        group_id: GroupId,
        user_id: UserId,
        audio: Request,
        sc_offset: Offset = None,
        sample_rate: SampleRate = 16000,
        language: Language = None,
    ):
        return cls(
            group_id=group_id,
            user_id=user_id,
            sc_offset=sc_offset,
            audio=await audio.body(),
            sample_rate=sample_rate,
            language=language,
        )


__all__ = [
    "LIDEmbedRequest",
    "LIDReferenceRequest",
    "LIDRequest",
]
