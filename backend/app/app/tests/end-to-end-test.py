import asyncio
import datetime
import json

from dotenv import load_dotenv

from app.base_types import CacheItem, NewsArticleSummary, NewsletterItem
from app.cache.redis.aio_redis_cache import AioRedisCache
from app.cache.redis.redis_utils import RedisConfig
from app.core.api_provider import APIProvider
from app.core.data_processors.openai.openai import OpenAI
from app.core.data_processors.openai.openai_utils import OpenAIConfig, OpenAIModels, OpenAIChatCompletion, OpenAIRoles
from app.core.data_providers.news_data_io.news_data_io import NewsDataIO
from app.core.data_providers.news_data_io.news_data_io_utils import NewsDataIOConfig
from app.core.newsletter_formatter import NewsletterFormatter
from app.core.selection_algos.duplicates_remover import DuplicatesRemover
from app.core.selection_algos.representative_items_algo import RepresentativeItemsAlgo
from app.utils import send_email

load_dotenv()


async def async_main():
    await full_test(search_term="space exploration")
    await full_test(search_term="computer science technology")


async def full_test(search_term):
    # todo: index articles by link and avoid inserting duplicates
    # todo: add a search-term emoji to the letter subject
    # todo: handle cases where the returned articles are more than the max allowed per user
    system_message = OpenAIChatCompletion(
        role=OpenAIRoles.SYSTEM,
        content=(
            f"You are an editor for a newsletter that summarizes articles in 200 words or less."
            f" The articles are derived using the search term {search_term}. The user will provide you with an article"
            " and you will reply in a JSON format like {\"title\": <SUMMARY TITLE>, \"summary\": <ARTICLE SUMMARY>}."
            " Feel free to break the summary into easily digestible paragraphs."
        ),
    )
    api_provider_ = APIProvider()

    news_data_io = NewsDataIO(api_provider=api_provider_, config=NewsDataIOConfig())
    response = await news_data_io.get_last_day_news(topic=search_term)

    openai = OpenAI(api_provider=api_provider_, config=OpenAIConfig())
    cache_config = RedisConfig()
    cache = AioRedisCache(config=cache_config)
    await cache.initialize()
    new_items = []

    for article in response:
        if not await cache.check_item_exists(article=article):
            embedding = await openai.get_embedding(model=OpenAIModels.TEXT_EMBEDDING_ADA_002, text=article.content)
            cache_item = CacheItem(article=article, embedding=embedding)
            await cache.store_item(cache_item=cache_item)
            new_items.append(cache_item)

    if len(new_items) > 0:
        await cache.clear_oldest_items(
            search_term=search_term,
            max_items_to_keep=cache_config.cache_items_per_user,  # todo: make on a per-user basis (?)
        )

        cache_items = await cache.get_items(search_term=search_term)

        duplicates_remover = DuplicatesRemover(openai=openai)
        representer = RepresentativeItemsAlgo(duplicates_remover=duplicates_remover)

        items = await representer.get_k_most_representative_items(new_items=new_items, cache_items=cache_items, k=5)
        article_summary_tasks = [
            openai.get_chat_completions(
                model=OpenAIModels.GPT_3_5_TURBO,
                messages=[system_message, OpenAIChatCompletion(role=OpenAIRoles.USER, content=item.article.content)],
            )
            for item in items
        ]
        article_summaries = await asyncio.gather(*article_summary_tasks)
        newsletter_items = []
        for summary, item in zip(article_summaries, items):
            content_json = json.loads(summary.content)
            newsletter_items.append(
                NewsletterItem(
                    article=item.article,
                    summary=NewsArticleSummary(summary_title=content_json["title"], summary=content_json["summary"]),
                )
            )

        newsletter_formatter = NewsletterFormatter()
        html = newsletter_formatter.format_newsletter_html(newsletter_items=newsletter_items)
        send_email(
            email_to="petioptrv@icloud.com",
            subject_template=f"{search_term} {datetime.datetime.today().strftime('%Y-%m-%d')}",
            html_template=html,
        )


def main():
    asyncio.run(async_main())


if __name__ == "__main__":
    # todo: make runs scheduled
    main()
