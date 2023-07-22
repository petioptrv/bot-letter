from typing import Dict, List, Optional

from app.core.api_provider import APIProvider
from app.core.data_providers.news_data_io.news_data_io_utils import NewsDataIOCategories, NewsDataIOConfig


class NewsDataIO:
    def __init__(self, api_provider: APIProvider, config: NewsDataIOConfig):
        self._api_provider = api_provider
        self._api_key = config.news_data_io_api_key
        self._base_url = "https://newsdata.io/api/1/news"

    async def get_last_day_news(
        self,
        topic: str,
        categories: Optional[List[NewsDataIOCategories]] = None,
    ) -> Dict:
        params = {
            "q": topic,
        }
        if categories is not None and len(categories) != 0:
            params["category"] = ",".join(categories)

        response = await self._api_provider.get(
            url=self._base_url,
            params=params,
            headers={"X-ACCESS-KEY": self._api_key},
        )

        return response


if __name__ == "__main__":
    import asyncio

    from dotenv import load_dotenv

    load_dotenv()

    news_data_io = NewsDataIO(api_provider=APIProvider(), config=NewsDataIOConfig())

    resp = asyncio.run(news_data_io.get_last_day_news(topic='"space industry"'))
    print(resp)
    print(f"len results: {len(resp['results'])}")
