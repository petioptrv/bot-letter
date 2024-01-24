import base64
import json
import logging
from typing import Dict, Optional

import aioredis
import numpy as np
from aioredis import Redis

from app.base_types import CacheItem, Embedding, NewsArticle, NewsArticleSummary
from app.cache.cache_base import CacheBase
from app.cache.redis.redis_utils import RedisConfig


class AioRedisCache(CacheBase):
    # todo: ensure there are no duplicated articles in the db
    # todo: ensure that a periodic cleanup is performed
    # todo: log stats about how long it takes to build one newsletter
    # todo: test that cache item is recovered ok

    def __init__(self, config: RedisConfig):
        self._redis_host = config.redis_host
        self._redis_port = config.redis_port
        self._redis_password = config.redis_password
        self._conn: Optional[Redis] = None

    async def initialize(self):
        self._conn = await aioredis.from_url(
            url=f"redis://{self._redis_host}:{self._redis_port}/0",
            password=self._redis_password,
            encoding="utf-8",
            decode_responses=True,
        )

    async def check_item_exists(self, article: NewsArticle) -> bool:
        item_name = article.article_id
        return await self._conn.exists(item_name)

    async def store_item(self, cache_item: CacheItem):
        item_name = cache_item.article.article_id
        if not await self._conn.exists(item_name):
            await self.update_item(cache_item=cache_item)

    async def update_item(self, cache_item: CacheItem):
        item = self._format_for_cache(cache_item=cache_item)
        item_name = cache_item.article.article_id
        await self._conn.hset(name=item_name, mapping=item)

    async def clear_all_items(self, newsletter_description: Optional[str]):
        await self.clear_oldest_items(
            newsletter_description=newsletter_description, max_items_to_keep=0
        )

    async def clear_oldest_items(
        self, newsletter_description: Optional[str], max_items_to_keep: int
    ):
        sorted_keys_items = await self._get_sorted_key_item_tuples(
            newsletter_description=newsletter_description
        )
        keys_to_remove = [key for key, _ in sorted_keys_items[max_items_to_keep:]]
        if len(keys_to_remove) != 0:
            await self._conn.delete(*keys_to_remove)

    async def clear_items_older_than(
        self, newsletter_description: Optional[str], latest_timestamp: float
    ):
        sorted_keys_items = await self._get_sorted_key_item_tuples(
            newsletter_description=newsletter_description
        )
        keys_to_remove = [
            key
            for key, item in sorted_keys_items
            if item.article.publishing_timestamp < latest_timestamp
        ]
        if len(keys_to_remove) != 0:
            await self._conn.delete(*keys_to_remove)

    async def get_items_since(
        self, newsletter_description: Optional[str], since_timestamp: float
    ) -> [CacheItem]:
        sorted_items = await self._get_sorted_key_item_tuples(
            newsletter_description=newsletter_description
        )
        items = [
            item
            for _, item in sorted_items
            if item.article.publishing_timestamp >= since_timestamp
        ]
        return items

    async def get_newest_item(
        self, newsletter_description: Optional[str]
    ) -> Optional[CacheItem]:
        sorted_items = await self._get_sorted_key_item_tuples(
            newsletter_description=newsletter_description
        )
        if len(sorted_items) != 0:
            newest_item = sorted_items[0][1]
        else:
            newest_item = None
        return newest_item

    async def get_items(self) -> [CacheItem]:
        keys = await self._get_item_keys()
        pipeline = self._conn.pipeline()
        for key in keys:
            await pipeline.hgetall(key)
        items = await pipeline.execute()
        cache_items = [self._format_from_cache(item) for item in items]
        return cache_items

    async def get_item_from_article(self, article: NewsArticle) -> Optional[CacheItem]:
        item_name = article.article_id
        item = await self._conn.hgetall(item_name)
        if item:
            cache_item = self._format_from_cache(item)
        else:
            cache_item = None
        return cache_item

    @staticmethod
    def _format_for_cache(cache_item: CacheItem) -> Dict:
        item = {
            "article": json.dumps(cache_item.article.dict()),
            "model": cache_item.embedding.model,
            "embedding": base64.b64encode(s=cache_item.embedding_vector.tobytes()),
            "title": cache_item.article.title,
            "article_summary": json.dumps(cache_item.article_summary.dict()),
        }
        return item

    async def _get_sorted_key_item_tuples(
        self, newsletter_description: Optional[str]
    ) -> [(str, CacheItem)]:
        keys = await self._get_item_keys()
        logging.getLogger(name=__name__).debug(msg=f"Found {len(keys)} keys in the cache")
        if keys:
            pipeline = self._conn.pipeline()
            for key in keys:
                await pipeline.hgetall(key)
            items = await pipeline.execute()
            items = [self._format_from_cache(item) for item in items]
            keys_items = zip(keys, items)

            sorted_keys_items = sorted(
                keys_items,
                key=lambda x: x[1].article.publishing_timestamp,
                reverse=True,
            )
        else:
            sorted_keys_items = []

        return sorted_keys_items

    async def _get_item_keys(self) -> [str]:
        item_key_matcher = "*"
        keys = await self._conn.keys(item_key_matcher)
        return keys

    @staticmethod
    def _format_from_cache(item: Dict) -> CacheItem:
        summary = json.loads(item["article_summary"])
        cache_item = CacheItem(
            article=json.loads(item["article"]),
            embedding=Embedding(
                vector=np.frombuffer(
                    base64.b64decode(s=item["embedding"]), dtype=np.float32
                ),
                model=item["model"],
            ),
            article_summary=NewsArticleSummary(
                summary_title=summary["summary_title"],
                summary=summary["summary"],
            ),
        )
        return cache_item
