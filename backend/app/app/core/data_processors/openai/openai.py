import json
from typing import Dict, List

from app.core.api_provider import APIProvider
from app.core.data_processors.openai.openai_utils import (
    OpenAIConfig,
    OpenAIModels,
    OpenAIChatCompletion,
)


class OpenAI:
    def __init__(self, api_provider: APIProvider, config: OpenAIConfig):
        self._api_provider = api_provider
        self._api_key = config.openai_api_key
        self._base_url = "https://api.openai.com/v1"

    async def get_models(self) -> Dict:
        url = f"{self._base_url}/models"
        headers = self._build_auth_headers()
        response = await self._api_provider.get(url=url, headers=headers)
        return response

    async def get_chat_completions(
        self,
        model: OpenAIModels,
        messages: List[OpenAIChatCompletion],
    ) -> Dict:
        url = f"{self._base_url}/chat/completions"
        headers = self._build_auth_headers()
        headers["Content-Type"] = "application/json"
        data = {
            "model": model.value,
            "messages": [message.dict() for message in messages],
        }
        response = await self._api_provider.post(
            url=url, headers=headers, data=json.dumps(data)
        )
        return response

    async def get_embedding(self, model: OpenAIModels, text: str) -> Dict:
        url = f"{self._base_url}/embeddings"
        headers = self._build_auth_headers()
        headers["Content-Type"] = "application/json"
        data = {
            "model": model.value,
            "input": text,
        }
        response = await self._api_provider.post(
            url=url, headers=headers, data=json.dumps(data)
        )
        return response

    def _build_auth_headers(self) -> Dict:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
        }
        return headers
