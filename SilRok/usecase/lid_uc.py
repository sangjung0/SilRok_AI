from sjpy.audio import s16le_bytes_to_array, resample_wav, mp4_bytes_to_ndarray

from SilRok.dto.request import LIDEmbedRequest, LIDReferenceRequest, LIDRequest
from SilRok.dto.response import LIDEmbedResponse, LIDResponse
from SilRok.services import LLMInput, LIDService, LLMService, llm_mode
from SilRok.utils import embedding_from_bytes


class LIDUC:
    def __init__(
        self,
        lid_service: LIDService,
        llm_service: LLMService,
        sample_rate: int,
        embedding_length: int,
    ):
        super().__init__()
        self.lid_service = lid_service
        self.llm_service = llm_service

        self.__sr = sample_rate
        self.__el = embedding_length

    async def stream(self, request: LIDRequest):
        audio = s16le_bytes_to_array(request.audio)
        audio = resample_wav(audio, request.sample_rate, self.__sr).reshape(-1)
        result = await self.lid_service.stream(
            request.group_id,
            request.user_id,
            audio,
            request.sc_offset,
            request.language,
        )

        if result.completed:
            await self.llm_service.request(
                LLMInput(
                    tid=request.group_id,
                    conversation="\n".join(
                        f"{s.speaker}: {s.text}" for s in result.completed
                    ),
                    mode=llm_mode.UPDATE,
                )
            )

        return LIDResponse.from_lid_sentence(result)

    async def reference(self, request: LIDReferenceRequest) -> None:
        # print("LIDUC.reference called")
        # print(f"request.user_ids: {request.user_ids} {len(request.refers)}")
        embedding = embedding_from_bytes(request.refers, request.counts, self.__el)
        await self.lid_service.update_embedding(
            request.group_id, request.user_ids, embedding
        )
        return None

    async def embedding(self, request: LIDEmbedRequest) -> LIDEmbedResponse:
        audio = mp4_bytes_to_ndarray(request.audio, self.__sr).reshape(-1)
        result = await self.lid_service.embedding("", audio)
        return LIDEmbedResponse.from_embedding(result).to_dict()


__all__ = ["LIDUC"]
