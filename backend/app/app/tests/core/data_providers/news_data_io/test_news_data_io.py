import pytest
from aioresponses import aioresponses

from app.core.api_provider import APIProvider
from app.core.data_providers.news_data_io.news_data_io_utils import NewsDataIOConfig
from app.core.data_providers.news_data_io.news_data_io import NewsDataIO


@pytest.mark.asyncio
async def test_get_last_day_news():
    with aioresponses() as mocked:
        url = "https://newsdata.io/api/1/news?q=OpenAI"
        mock_response = {"status": "ok", "totalResults": 1, "articles": [{"title": "Test Article"}]}
        mocked.get(url, status=200, payload=mock_response)

        api_provider = APIProvider()
        config = NewsDataIOConfig(news_data_io_api_key="test-api-key")
        client = NewsDataIO(api_provider=api_provider, config=config)
        response = await client.get_last_day_news(topic="OpenAI")

        assert response == mock_response


@pytest.mark.asyncio
async def test_get_last_day_news_error():
    with aioresponses() as mocked:
        url = "https://newsdata.io/api/1/news?q=OpenAI"
        mocked.get(url, status=500)

        api_provider = APIProvider()
        config = NewsDataIOConfig(news_data_io_api_key="test-api-key")
        client = NewsDataIO(api_provider=api_provider, config=config)

        with pytest.raises(Exception):
            await client.get_last_day_news(topic="OpenAI")
