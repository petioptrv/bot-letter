import asyncio
import datetime
import logging
import time
from typing import Optional, List

from dotenv import load_dotenv

from app.base_types import CacheItem, NewsArticleSummary, NewsletterItem
from app.cache.redis.aio_redis_cache import AioRedisCache
from app.cache.redis.redis_utils import redis_config
from app.core.api_provider import APIProvider
from app.core.data_processors.openai.openai import OpenAI
from app.core.data_processors.openai.openai_utils import (
    OpenAIConfig,
    OpenAIModels,
    OpenAIChatCompletion,
    OpenAIRoles,
)
from app.core.data_providers.news_data_io.news_data_io import NewsDataIO
from app.core.data_providers.news_data_io.news_data_io_utils import (
    news_data_io_config,
)
from app.core.newsletter_creator.newsletter_creator_utils import newsletter_creator_config
from app.core.newsletter_formatter import NewsletterFormatter
from app.core.selection_algos.duplicates_remover import DuplicatesRemover
from app.core.selection_algos.representative_items_algo import RepresentativeItemsAlgo
from app.utils import send_email

load_dotenv()


async def generate_newsletter(search_term: str, user_id: int):
    # todo: index articles by title and avoid inserting duplicates
    # todo: detect if any of the articles duplicate with previously sent articles
    # todo: add a search-term emoji to the letter subject
    # todo: handle cases where the returned articles are more than the max allowed per user
    # todo: deal with the case where the prompt is way too long and no tokens are left for the completion ---
    #       one way to do it is to break up the article into paragraphs and summarize each paragraph separately
    #       and then combine the summaries into one summary.

    newsletter_generation_id = f"{user_id}_{user_id}_{int(time.time())}"
    log_for_newsletter_generation(
        level=logging.INFO,
        generation_id=newsletter_generation_id,
        message=f"Starting full test for search term {search_term}",
    )

    prompt = newsletter_creator_config.prompt.format(
        word_count=newsletter_creator_config.word_count,
        search_term=search_term,
    )
    system_message = OpenAIChatCompletion(role=OpenAIRoles.SYSTEM, content=prompt)
    api_provider_ = APIProvider()

    news_data_io = NewsDataIO(api_provider=api_provider_, config=news_data_io_config)
    response = await news_data_io.get_last_day_news(topic=search_term)

    log_for_newsletter_generation(
        level=logging.DEBUG,
        generation_id=newsletter_generation_id,
        message=f"Got {len(response.results)} articles from NewsDataIO for search term {search_term}",
    )

    openai = OpenAI(api_provider=api_provider_, config=OpenAIConfig())
    cache = AioRedisCache(config=redis_config)
    await cache.initialize()
    new_items = []

    for article in response.results:
        if not await cache.check_item_exists(article=article):
            try:
                embedding = await openai.get_embedding(
                    model=OpenAIModels.TEXT_EMBEDDING_ADA_002, text=article.content
                )
            except IOError as e:
                log_for_newsletter_generation(
                    level=logging.ERROR,
                    generation_id=newsletter_generation_id,
                    message=f"Failed to get embedding for article {article}",
                    exc_info=e,
                )
            else:
                cache_item = CacheItem(article=article, embedding=embedding)
                await cache.store_item(cache_item=cache_item)
                new_items.append(cache_item)
        else:
            log_for_newsletter_generation(
                level=logging.INFO,
                generation_id=newsletter_generation_id,
                message=f"Article {article.title} already exists in cache for search term {search_term}",
            )
            new_items.append(await cache.get_item_from_article(article=article))

    if len(new_items) > 0:
        await cache.clear_oldest_items(search_term=search_term, max_items_to_keep=redis_config.cache_items_per_user)

        cache_items = await cache.get_items(search_term=search_term)

        duplicates_remover = DuplicatesRemover(openai=openai)
        representer = RepresentativeItemsAlgo(duplicates_remover=duplicates_remover)

        items: List[CacheItem] = await representer.get_k_most_representative_items(
            new_items=new_items, cache_items=cache_items, k=5
        )

        log_for_newsletter_generation(
            level=logging.INFO,
            generation_id=newsletter_generation_id,
            message=f"Got {len(items)} representative items for search term {search_term}",
        )

        article_summary_tasks = [
            openai.get_chat_completions(
                model=OpenAIModels.GPT_3_5_TURBO,
                messages=[
                    system_message,
                    OpenAIChatCompletion(
                        role=OpenAIRoles.USER, content=item.article.content
                    ),
                ],
            )
            for item in items
        ]
        article_summaries = await asyncio.gather(
            *article_summary_tasks, return_exceptions=True
        )
        newsletter_items = []
        for summary, item in zip(article_summaries, items):
            try:
                if isinstance(summary, Exception):
                    raise summary
                newsletter_items.append(
                    NewsletterItem(
                        article=item.article,
                        summary=NewsArticleSummary(
                            summary_title=item.article.title,
                            summary=summary.content,
                        ),
                    )
                )
            except Exception as e:
                log_for_newsletter_generation(
                    level=logging.ERROR,
                    generation_id=newsletter_generation_id,
                    message=(
                        f"Failed to parse summary for article {item.article}"
                    ),
                    exc_info=e,
                )

        newsletter_formatter = NewsletterFormatter()
        html = newsletter_formatter.format_newsletter_html(
            newsletter_items=newsletter_items
        )
        send_email(
            email_to="petioptrv@icloud.com",
            subject_template=f"{search_term} {datetime.datetime.today().strftime('%Y-%m-%d')}",
            html_template=html,
        )


def log_for_newsletter_generation(
    level: int, generation_id: str, message: str, exc_info: Optional[Exception] = None
):
    logging.getLogger(__name__).log(level=level, msg=f"ng-{generation_id}: {message}", exc_info=exc_info)


def main():
    asyncio.run(generate_newsletter(search_term='"space industry"', user_id=0))


if __name__ == "__main__":
    # todo: make runs scheduled
    main()
