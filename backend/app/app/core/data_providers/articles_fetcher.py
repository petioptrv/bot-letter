import logging
import time

from app.base_types import CacheItem
from app.cache.redis.aio_redis_cache import AioRedisCache
from app.cache.redis.redis_utils import redis_config
from app.core.api_provider import APIProvider
from app.core.data_processors.openai.openai import OpenAI
from app.core.data_processors.openai.openai_utils import openai_config, OpenAIModels
from app.core.data_providers.news_data_io.news_data_io import NewsDataIO
from app.core.data_providers.news_data_io.news_data_io_utils import news_data_io_config


async def update_articles_database():
    # todo: index articles by title and avoid inserting duplicates
    # todo: consider filtering articles published by several news outlets (i.e. exact same article, but diff urls)

    logging.getLogger(name=__name__).info(msg="Starting articles database update")

    api_provider = APIProvider()
    news_data_io = NewsDataIO(api_provider=api_provider, config=news_data_io_config)
    cache = AioRedisCache(config=redis_config)
    openai = OpenAI(api_provider=api_provider, config=openai_config)
    current_timestamp = time.time()

    await cache.initialize()

    latest_timestamp = (
        current_timestamp - 2 * 24 * 60 * 60
    )  # keep two days worth of articles
    await cache.clear_items_older_than(
        search_term=None, latest_timestamp=latest_timestamp
    )

    newest_item = await cache.get_newest_item(search_term=None)
    if newest_item is None:
        last_timestamp = int(time.time() - 24 * 60 * 60)
    else:
        last_timestamp = int(newest_item.article.publishing_timestamp)
    response = await news_data_io.get_latest_news(start_from_ts=last_timestamp)

    logging.getLogger(name=__name__).info(
        msg=f"Got {len(response.results)} articles from NewsDataIO"
    )

    for article in response.results:
        if not await cache.check_item_exists(article=article):
            try:
                embedding = await openai.get_embedding(
                    model=OpenAIModels.TEXT_EMBEDDING_ADA_002, text=article.content
                )
            except IOError:
                logging.getLogger(name=__name__).exception(
                    msg=f"Failed to get embedding for article {article}"
                )
            else:
                cache_item = CacheItem(article=article, embedding=embedding)
                await cache.store_item(cache_item=cache_item)
        else:
            logging.getLogger(name=__name__).info(
                msg=f"Article {article.title} already exists in cache"
            )

    logging.getLogger(name=__name__).info(msg="Finished articles database update")


if __name__ == "__main__":
    import asyncio

    asyncio.run(update_articles_database())
