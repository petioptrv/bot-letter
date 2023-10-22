import asyncio
import logging
import sys
import time
from datetime import datetime
from typing import Dict, List, Optional

import pytz

from app.core.api_provider import APIProvider
from app.core.data_providers.news_data_io.news_data_io_utils import (
    NewsDataIOCategories,
    NewsDataIOConfig,
)
from app.base_types import NewsArticle, NewsArticleSearchResults


class NewsDataIO:
    def __init__(self, api_provider: APIProvider, config: NewsDataIOConfig):
        self._api_provider = api_provider
        self._api_key = config.news_data_io_api_key
        self._base_url = "https://newsdata.io/api/1/news"

    async def get_latest_news(
        self,
        topic: Optional[str] = None,
        categories: Optional[List[NewsDataIOCategories]] = None,
        max_page_count: int = sys.maxsize,
        language: str = "en",
        start_from_ts: Optional[int] = None,
    ) -> NewsArticleSearchResults:
        if start_from_ts is None:
            start_from_ts = int(time.time() - 24 * 60 * 60)
        articles_data = await self._get_news_data(
            topic=topic,
            categories=categories,
            max_page_count=max_page_count,
            language=language,
            start_from_ts=start_from_ts,
        )
        articles = [
            NewsArticle(
                title=article["title"],
                url=article["link"],
                image_url=article["image_url"],
                newsletter_description=topic,
                publishing_timestamp=self._to_utc_timestamp(
                    pub_date_string=article["pubDate"]
                ),
                description=article["description"],
                content=article["content"],
            )
            for article in articles_data["results"]
            if article["content"] is not None and article["description"] is not None
        ]
        result = NewsArticleSearchResults(
            total_results_count=articles_data["totalResults"], results=articles
        )

        return result

    async def _get_news_data(
        self,
        topic: Optional[str],
        categories: Optional[List[NewsDataIOCategories]],
        max_page_count: int,
        language: str,
        start_from_ts: int,
    ) -> Dict:

        timeframe_minutes = int((time.time() - start_from_ts) // 60)
        timeframe = f"{timeframe_minutes + 1}m"
        params = {
            "language": language,
            "timeframe": timeframe,
            "timezone": "UTC",
        }
        if topic is not None and len(topic) != 0:
            params["q"] = topic
        if categories is not None and len(categories) != 0:
            params["category"] = ",".join(categories)

        responses = {}
        done = False
        while not done:
            try:
                response = await self._api_provider.get(
                    url=self._base_url,
                    params=params,
                    headers={"X-ACCESS-KEY": self._api_key},
                )
            except Exception as e:
                logging.getLogger(__name__).exception(f"Failed to get news data")
                raise e
            if len(responses) == 0:
                responses = response
            else:
                responses["results"].extend(response["results"])
            params["page"] = response["nextPage"]
            earliest_timestamp = self._to_utc_timestamp(pub_date_string=response["results"][-1]["pubDate"])
            done = (
                len(response["results"]) >= max_page_count
                or response["nextPage"] is None
                or earliest_timestamp < start_from_ts
            )
            if not done:
                await asyncio.sleep(1)

        return responses

    @staticmethod
    def _to_utc_timestamp(pub_date_string: str) -> int:
        utc_dt = datetime.strptime(pub_date_string, "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.utc)
        timestamp = int(utc_dt.timestamp())
        return timestamp
