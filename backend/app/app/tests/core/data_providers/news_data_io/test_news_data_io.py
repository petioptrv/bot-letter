import pytest

from app.core.api_provider import APIProvider
from app.core.data_providers.news_data_io.news_data_io_utils import NewsDataIOConfig
from app.core.data_providers.news_data_io.news_data_io import NewsDataIO
from app.tests.testing_utils import APIProviderMocker


@pytest.mark.asyncio
async def test_get_last_day_news(api_provider_mock: APIProviderMocker):
    url = "https://newsdata.io/api/1/news?q=OpenAI"
    mock_response = {
        "status": "ok",
        "totalResults": 1,
        "results": [
            {
                "title": "Test Article",
                "link": "https://test-article.com",
                "image_url": "https://test-article.com/image.jpg",
                "pubDate": "2021-02-03 04: 05: 06",
                "content": "Test content",
            }
        ],
        "nextPage": None,
    }
    api_provider_mock.get(url, status=200, payload=mock_response)

    api_provider = APIProvider()
    config = NewsDataIOConfig(news_data_io_api_key="test-api-key")
    client = NewsDataIO(api_provider=api_provider, config=config)
    response = await client.get_last_day_news(topic="OpenAI")

    assert len(response) == 1

    article = response[0]

    assert article.title == "Test Article"
    assert article.url == "https://test-article.com"
    assert article.image_url == "https://test-article.com/image.jpg"
    assert article.search_term == "OpenAI"
    assert article.publishing_timestamp == 1612343106
    assert article.content == "Test content"


@pytest.mark.asyncio
async def test_get_last_day_news_error(api_provider_mock: APIProviderMocker):
    url = "https://newsdata.io/api/1/news?q=OpenAI"
    api_provider_mock.get(url, status=500)

    api_provider = APIProvider()
    config = NewsDataIOConfig(news_data_io_api_key="test-api-key")
    client = NewsDataIO(api_provider=api_provider, config=config)

    with pytest.raises(Exception):
        await client.get_last_day_news(topic="OpenAI")


# if __name__ == "__main__":
#     import asyncio
#     from pprint import pprint
#
#     from dotenv import load_dotenv
#
#     load_dotenv()
#
#     news_data_io = NewsDataIO(api_provider=APIProvider(), config=NewsDataIOConfig())
#
#     resp = asyncio.run(news_data_io.get_last_day_news(topic='"space exploration"'))
#     pprint(resp)
#     print(f"len results: {len(resp['results'])}")
