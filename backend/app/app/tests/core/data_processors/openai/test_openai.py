import numpy as np
import pytest
from numpy import testing

from app.core.api_provider import APIProvider
from app.core.data_processors.openai.openai import OpenAI
from app.core.data_processors.openai.openai_utils import (
    OpenAIConfig,
    OpenAIModels,
    OpenAIRoles,
    OpenAIChatCompletion,
)
from app.tests.testing_utils import compile_url_matcher, APIProviderMocker
from app.base_types import Embedding


@pytest.mark.asyncio
async def test_get_models(api_provider_mock: APIProviderMocker):
    mock_models_response = {
        "models": [
            {
                "id": "text-davinci-002",
                "object": "text.completion",
                "created": 1627913816,
            },
            {
                "id": "text-curie-002",
                "object": "text.completion",
                "created": 1627913816,
            },
        ]
    }
    url = compile_url_matcher(url="https://api.openai.com/v1/models")
    api_provider_mock.get(url, status=200, payload=mock_models_response)

    api_provider = APIProvider()
    config = OpenAIConfig(openai_api_key="test-api-key")
    client = OpenAI(api_provider=api_provider, config=config)
    response = await client.get_models()

    assert response == mock_models_response


@pytest.mark.asyncio
async def test_get_chat_completions(api_provider_mock: APIProviderMocker):
    mock_completions_response = {
        "id": "chatcmpl-2n0QLPZ3NeFgmOoXbbT21uh9oWGTJ",
        "object": "chat.completion",
        "created": 1627913816,
        "model": "gpt-3.5-turbo",
        "usage": {"prompt_tokens": 56, "completion_tokens": 31, "total_tokens": 87},
        "choices": [
            {
                "message": {
                    "role": "system",
                    "content": "You are a helpful assistant.",
                },
                "finish_reason": "stop",
                "index": 0,
            }
        ],
    }
    model = OpenAIModels.GPT_4
    messages = [
        OpenAIChatCompletion(
            role=OpenAIRoles.SYSTEM, content="You are a helpful assistant."
        )
    ]
    url = compile_url_matcher(url=f"https://api.openai.com/v1/chat/completions")
    api_provider_mock.post(url, status=200, payload=mock_completions_response)

    api_provider = APIProvider()
    config = OpenAIConfig(openai_api_key="test-api-key")
    client = OpenAI(api_provider=api_provider, config=config)
    response = await client.get_chat_completions(model=model, messages=messages)

    assert response == mock_completions_response


@pytest.mark.asyncio
async def test_get_embedding(api_provider_mock: APIProviderMocker):
    mock_response = {
        "object": "list",
        "data": [
            {
                "object": "embedding",
                "embedding": [
                    0.0023064255,
                    -0.009327292,
                    -0.0028842222,
                ],
                "index": 0,
            }
        ],
        "model": "text-embedding-ada-002",
        "usage": {"prompt_tokens": 8, "total_tokens": 8},
    }
    url = compile_url_matcher(url=f"https://api.openai.com/v1/embeddings")
    api_provider_mock.post(url, status=200, payload=mock_response)

    api_provider = APIProvider()
    config = OpenAIConfig(openai_api_key="test-api-key")
    client = OpenAI(api_provider=api_provider, config=config)
    response = await client.get_embedding(
        model=OpenAIModels.TEXT_EMBEDDING_ADA_002, text="OpenAI"
    )
    expected_array = np.array(
        mock_response["data"][0]["embedding"], dtype=np.float32
    ).tobytes()

    assert isinstance(response, Embedding)
    assert response.vector == expected_array
    assert response.model == "text-embedding-ada-002"


if __name__ == "__main__":
    import asyncio

    api_provider_ = APIProvider()
    openai = OpenAI(api_provider=api_provider_, config=OpenAIConfig())

    models = asyncio.run(openai.get_models())
    print(models)

    text = (
        "Received as a part of the SPARK grants by iDEX, Pixxel said the grant will"
        " help it develop small satellites of up to 150 kgs for electro-optical,"
        " infrared, synthetic aperture radar and hyper spectral purposes."
    )

    embedding = asyncio.run(
        openai.get_embedding(model=OpenAIModels.TEXT_EMBEDDING_ADA_002, text=text)
    )
    print(embedding)

    messages = [
        OpenAIChatCompletion(
            role=OpenAIRoles.SYSTEM,
            content=(
                """You are a newsletter creator. I will give you the summaries of
a certain number of articles (I will tell you how many) along with
their links that I will send to you in this chat, you won't have to
browse the web for them yourself. You have to read the articles and
select 5 that seem most important and impactful, then you have to
give a summary for each article. Each summary should be a maximum of
300 words. You should also provide the link to the article in the
form {'summary': YOUR_SUMMARY, 'link': ARTICLE_LINK}. Do you have
any clarification questions?"""
            ),
        )
    ]
    completions = asyncio.run(
        openai.get_chat_completions(model=OpenAIModels.GPT_4, messages=messages)
    )
    print(completions)
