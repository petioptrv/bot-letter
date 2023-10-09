import json
from typing import Dict, List

import numpy as np

from app.core.api_provider import APIProvider
from app.core.data_processors.openai.openai_utils import (
    OpenAIConfig,
    OpenAIModels,
    OpenAIChatCompletion,
    OpenAIRoles,
)
from app.base_types import Embedding


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
    ) -> OpenAIChatCompletion:
        # todo: attach user IDs to requests: https://platform.openai.com/docs/guides/safety-best-practices/end-user-ids
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
        completion = OpenAIChatCompletion(
            role=OpenAIRoles(response["choices"][0]["message"]["role"]),
            content=response["choices"][0]["message"]["content"],
        )
        return completion

    async def get_embedding(self, model: OpenAIModels, text: str) -> Embedding:
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
        vector = np.array(response["data"][0]["embedding"], dtype=np.float32)
        embedding = Embedding(vector=vector, model=model)
        return embedding

    def _build_auth_headers(self) -> Dict:
        headers = {
            "Authorization": f"Bearer {self._api_key}",
        }
        return headers


if __name__ == "__main__":
    import asyncio
    import pprint

    openai_ = OpenAI(api_provider=APIProvider(), config=OpenAIConfig())
    pprint.pprint(asyncio.run(openai_.get_models()), indent=2)
