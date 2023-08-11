import sys
from datetime import datetime
from typing import Dict, List, Optional

from app.core.api_provider import APIProvider
from app.core.data_providers.news_data_io.news_data_io_utils import NewsDataIOCategories, NewsDataIOConfig
from app.base_types import NewsArticle


class NewsDataIO:
    def __init__(self, api_provider: APIProvider, config: NewsDataIOConfig):
        self._api_provider = api_provider
        self._api_key = config.news_data_io_api_key
        self._base_url = "https://newsdata.io/api/1/news"

    async def get_last_day_news(
        self,
        topic: str,
        categories: Optional[List[NewsDataIOCategories]] = None,
        max_page_count: int = sys.maxsize,
    ) -> List[NewsArticle]:
        # todo: consider filtering articles published by several news outlets (i.e. exact same article, but diff urls)
        articles_data = await self._get_news_data(
            topic=topic, categories=categories, max_page_count=max_page_count
        )
        articles = [
            NewsArticle(
                title=article["title"],
                url=article["link"],
                image_url=article["image_url"],
                search_term=topic,
                publishing_timestamp=self._to_utc_timestamp(pub_date_string=article["pubDate"]),
                content=article["content"],
            )
            for article in articles_data["results"]
            if article["content"] is not None
        ]

        return articles

    async def _get_news_data(
        self,
        topic: str,
        categories: Optional[List[NewsDataIOCategories]],
        max_page_count: int,
    ) -> Dict:
        params = {
            "q": topic,
        }
        if categories is not None and len(categories) != 0:
            params["category"] = ",".join(categories)

        remaining_page_count = max_page_count
        responses = {}
        done = False
        while not done:
            response = await self._api_provider.get(
                url=self._base_url,
                params=params,
                headers={"X-ACCESS-KEY": self._api_key},
            )
            if len(responses) == 0:
                responses = response
            else:
                responses["results"].extend(response["results"])
            params["page"] = response["nextPage"]
            done = remaining_page_count == 0 or response["nextPage"] is None

        return responses

    @staticmethod
    def _to_utc_timestamp(pub_date_string: str) -> int:
        timestamp = int(datetime.strptime(pub_date_string, "%Y-%m-%d %H:%M:%S").timestamp())
        return timestamp
