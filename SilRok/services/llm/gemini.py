import vertexai

from vertexai.generative_models import GenerativeModel, GenerationConfig
from google.oauth2 import service_account

DEFAULT_CONFIG = {
    "model_name": "gemini-2.5-flash",
    "generation_config": GenerationConfig(temperature=0.0, max_output_tokens=8192),
}


class Gemini:
    def __init__(
        self,
        google_cloud_project_id: str,
        google_cloud_location: str,
        google_cloud_service_account_path: str,
        genai_model_config: dict | None = None,
    ):
        super().__init__()
        genai_model_config = genai_model_config or DEFAULT_CONFIG

        credentials = service_account.Credentials.from_service_account_file(
            google_cloud_service_account_path
        )
        vertexai.init(
            project=google_cloud_project_id,
            location=google_cloud_location,
            credentials=credentials,
        )
        self.__gemini = GenerativeModel(**genai_model_config)

    def generate(self, history: list = []):
        return self.__gemini.start_chat(history=history, response_validation=False)


__all__ = ["Gemini"]
