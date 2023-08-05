import base64
import json
from typing import Dict, Optional

import aioredis
import numpy as np
from aioredis import Redis

from app.base_types import CacheItem, Embedding, NewsArticle
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
            url=f"redis://{self._redis_host}:{self._redis_port}",
            password=self._redis_password,
            encoding="utf-8",
            decode_responses=True,
        )

    async def check_item_exists(self, article: NewsArticle) -> bool:
        item_name = await self._build_item_name(article=article)
        return await self._conn.exists(item_name)

    async def store_item(self, cache_item: CacheItem):
        item = self._format_for_cache(cache_item=cache_item)
        item_name = await self._build_item_name(article=cache_item.article)
        if not await self._conn.exists(item_name):
            await self._conn.hset(name=item_name, mapping=item)

    async def clear_oldest_items(self, search_term: str, max_items_to_keep: int):
        item_name_prefix = self._build_item_name_prefix(search_term=search_term)
        keys = await self._conn.keys(f"{item_name_prefix}:*")
        pipeline = self._conn.pipeline()
        for key in keys:
            await pipeline.hgetall(key)
        items = await pipeline.execute()
        keys_items = zip(keys, items)
        sorted_keys_items = sorted(
            keys_items, key=lambda x: json.loads(x[1]["article"])["publishing_timestamp"], reverse=False
        )
        keys_to_remove = [key for key, _ in sorted_keys_items[:-max_items_to_keep]]
        if len(keys_to_remove) != 0:
            await self._conn.delete(*keys_to_remove)

    async def get_items(self, search_term: str) -> [CacheItem]:
        item_name_prefix = self._build_item_name_prefix(search_term=search_term)
        keys = await self._conn.keys(f"{item_name_prefix}:*")
        pipeline = self._conn.pipeline()
        for key in keys:
            await pipeline.hgetall(key)
        items = await pipeline.execute()
        cache_items = [self._format_from_cache(item) for item in items]
        return cache_items

    async def get_item_from_article(self, article: NewsArticle) -> Optional[CacheItem]:
        item_name = await self._build_item_name(article=article)
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
        }
        return item

    async def _build_item_name(self, article: NewsArticle) -> str:
        item_name_prefix = self._build_item_name_prefix(search_term=article.search_term)
        item_name_numeric = "".join(
            [hex(ord(char))[2:].zfill(2) for char in article.url]
        )
        name = f"{item_name_prefix}:{item_name_numeric}"
        return name

    @staticmethod
    def _build_item_name_prefix(search_term: str) -> str:
        item_name_prefix = f"{search_term}"
        return item_name_prefix

    @staticmethod
    def _format_from_cache(item: Dict) -> CacheItem:
        cache_item = CacheItem(
            article=json.loads(item["article"]),
            embedding=Embedding(
                vector=np.frombuffer(base64.b64decode(s=item["embedding"]), dtype=np.float32),
                model=item["model"],
            ),
        )
        return cache_item
