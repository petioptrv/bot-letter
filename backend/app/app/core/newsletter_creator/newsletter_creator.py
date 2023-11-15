import asyncio
import logging
import time
from itertools import chain, islice
from typing import Optional

from dotenv import load_dotenv

from app.base_types import NewsArticleSummary, NewsletterItem
from app.cache.redis.aio_redis_cache import AioRedisCache
from app.cache.redis.redis_utils import redis_config
from app.core.api_provider import APIProvider
from app.core.config import settings
from app.core.data_processors.openai.openai import OpenAI
from app.core.data_processors.openai.openai_utils import (
    OpenAIModels,
    OpenAIChatCompletion,
    OpenAIRoles,
    openai_config,
)
from app.core.newsletter_creator.newsletter_creator_utils import (
    newsletter_creator_config,
)
from app.core.newsletter_formatter import NewsletterFormatter
from app.core.selection_algos.representative_items_algo import (
    generate_most_representative_items,
)
from app.utils import send_email

load_dotenv()


async def generate_newsletter(newsletter_description: str, user_id: int, email: str):
    # todo: add a search-term emoji to the letter subject
    api_provider_ = APIProvider()
    openai = OpenAI(api_provider=api_provider_, config=openai_config)
    cache = AioRedisCache(config=redis_config)

    await cache.initialize()

    newsletter_generation_id = f"{user_id}_{user_id}_{int(time.time())}"
    log_for_newsletter_generation(
        level=logging.INFO,
        generation_id=newsletter_generation_id,
        message=(
            f'Starting newsletter creation for search description "{newsletter_description}"'
            f"\nMax wordcount per article: {newsletter_creator_config.word_count}"
        ),
    )

    # 2. For each article
    #   2.2. Ask ChatGPT if the current article makes sense as part of the newsletter
    #     2.2.1. If it does not, skip it
    #   2.3. For each of the previous articles
    #     2.3.1. Ask ChatGPT if the current one is redundant with the previous one
    #       2.3.1.1. If it is, skip it

    article_summary_prompt = newsletter_creator_config.summary_prompt.format(
        word_count=newsletter_creator_config.word_count,
    )
    article_summary_system_message = OpenAIChatCompletion(
        role=OpenAIRoles.SYSTEM, content=article_summary_prompt
    )

    newsletter_description_embedding = await openai.get_embedding(
        model=OpenAIModels.TEXT_EMBEDDING_ADA_002, text=newsletter_description
    )

    since_timestamp = time.time() - settings.ARTICLES_FETCH_WINDOW
    irrelevant_articles_count = 0
    news_items = await cache.get_items_since(
        newsletter_description=None, since_timestamp=since_timestamp
    )

    if len(news_items) == 0:
        new_items_log_level = logging.WARNING
    else:
        new_items_log_level = logging.DEBUG
    log_for_newsletter_generation(
        level=new_items_log_level,
        generation_id=newsletter_generation_id,
        message=f"Retrieved {len(news_items)} new items since {since_timestamp}",
    )

    relevant_candidates = []
    irrelevant_candidates = []
    if len(news_items) > 0:
        representative_items_generator = generate_most_representative_items(
            target_vector=newsletter_description_embedding.vector,
            cache_items=news_items,
        )

        async for item in representative_items_generator:
            try:
                if (
                    irrelevant_articles_count
                    == newsletter_creator_config.max_irrelevant_articles_count
                ):
                    break
                relevancy_prompt = (
                    newsletter_creator_config.article_relevancy_prompt.format(
                        newsletter_description=newsletter_description,
                        current_article_summary=item.article.description,
                    )
                )
                relevancy_completion = OpenAIChatCompletion(
                    role=OpenAIRoles.USER, content=relevancy_prompt
                )
                relevancy_response = await openai.get_chat_completions(
                    model=OpenAIModels.GPT_4_TURBO,
                    messages=[relevancy_completion],
                )
                if relevancy_response.content.lower() in ["no", "no."]:
                    irrelevant_articles_count += 1
                    log_for_newsletter_generation(
                        level=logging.DEBUG,
                        generation_id=newsletter_generation_id,
                        message=(
                            f"\nArticle not relevant:\n\n{item.article.title}\n{item.article.description}"
                            f"\n\nirrelevant_articles_count={irrelevant_articles_count}"
                        ),
                    )
                    irrelevant_candidates.append(item)
                    continue  # skip article
                if len(relevant_candidates) == 0:
                    relevant_candidates.append(item)
                else:
                    include = True
                    for previous_newsletter_item in chain(
                        relevant_candidates, irrelevant_candidates
                    ):
                        redundancy_prompt = newsletter_creator_config.article_redundancy_prompt.format(
                            previous_article_summary=previous_newsletter_item.article.description,
                            current_article_summary=item.article.description,
                        )
                        redundancy_completion = OpenAIChatCompletion(
                            role=OpenAIRoles.USER, content=redundancy_prompt
                        )
                        redundancy_response = await openai.get_chat_completions(
                            model=OpenAIModels.GPT_4_TURBO,
                            messages=[redundancy_completion],
                        )
                        if redundancy_response.content.lower() in ["yes", "yes."]:
                            include = False
                            irrelevant_articles_count += 1
                            log_for_newsletter_generation(
                                level=logging.DEBUG,
                                generation_id=newsletter_generation_id,
                                message=(
                                    f"\nArticle redundant:\n\n{item.article.title}\n{item.article.description}"
                                    f"\n\nirrelevant_articles_count={irrelevant_articles_count}"
                                ),
                            )
                            break  # skip article
                    if include:
                        log_for_newsletter_generation(
                            level=logging.DEBUG,
                            generation_id=newsletter_generation_id,
                            message=f"\nRelevant article:\n\n{item.article.title}\n{item.article.description}",
                        )
                        relevant_candidates.append(item)
            except IOError as e:
                if "Rate limit reached" in str(e):
                    await asyncio.sleep(1)
                else:
                    log_for_newsletter_generation(
                        level=logging.ERROR,
                        generation_id=newsletter_generation_id,
                        message=f"Failed to parse summary for article {item.article}",
                        exc_info=e,
                    )
            except Exception as e:
                log_for_newsletter_generation(
                    level=logging.ERROR,
                    generation_id=newsletter_generation_id,
                    message=f"Failed to parse summary for article {item.article}",
                    exc_info=e,
                )
            if (
                len(relevant_candidates)
                == newsletter_creator_config.max_articles_per_newsletter
            ):
                break

    newsletter_items = []
    for candidate in islice(
        chain(relevant_candidates, irrelevant_candidates),
        newsletter_creator_config.max_articles_per_newsletter,
    ):
        article_summary = candidate.article_summary
        if not article_summary.is_initialized:
            summary_content = await openai.get_chat_completions(
                model=OpenAIModels.GPT_4_TURBO,
                messages=[
                    article_summary_system_message,
                    OpenAIChatCompletion(
                        role=OpenAIRoles.USER,
                        content=candidate.article.content,
                    ),
                ],
            )
            article_summary.summary_title = candidate.article.title
            article_summary.summary = summary_content.content
            await cache.update_item(cache_item=candidate)
        newsletter_items.append(
            NewsletterItem(
                article=candidate.article,
                summary=NewsArticleSummary(
                    summary_title=candidate.article.title,
                    summary=article_summary.summary,
                ),
                relevant=candidate in relevant_candidates,
            )
        )

    if len(newsletter_items) != 0:
        newsletter_subject_prompt = (
            newsletter_creator_config.newsletter_subject_prompt.format(
                newsletter_content="\n\n".join(
                    [item.summary.summary for item in newsletter_items if item.relevant]
                )
            )
        )
        subject_completion = OpenAIChatCompletion(
            role=OpenAIRoles.USER, content=newsletter_subject_prompt
        )
        subject_response = await openai.get_chat_completions(
            model=OpenAIModels.GPT_4_TURBO, messages=[subject_completion]
        )
        newsletter_subject = subject_response.content

        newsletter_formatter = NewsletterFormatter()
        html = await newsletter_formatter.format_newsletter_html(
            api_provider=api_provider_, newsletter_items=newsletter_items, newsletter_description=newsletter_description
        )
    else:
        log_for_newsletter_generation(
            level=logging.INFO,
            generation_id=newsletter_generation_id,
            message=f"No new articles found for search term {newsletter_description}",
        )
        newsletter_subject = "No new articles."
        newsletter_formatter = NewsletterFormatter()
        html = newsletter_formatter.format_newsletter_html_no_new_articles(
            newsletter_description=newsletter_description
        )

    send_email(
        email_to=email,
        subject_template=newsletter_subject,
        html_template=html,
    )


def log_for_newsletter_generation(
    level: int, generation_id: str, message: str, exc_info: Optional[Exception] = None
):
    logging.getLogger(__name__).log(
        level=level, msg=f"ng-{generation_id}: {message}", exc_info=exc_info
    )


if __name__ == "__main__":
    # newsletter_description_ = (
    #     "I want a newsletter about the space sector industry. I am interested in the"
    #     " private space sector, but I also want to know what new government"
    #     " regulations are put in place that will affect the private space industry."
    #     " Topics that interest me are Space Exploration Sector, Orbital Industry,"
    #     " Commercial Space Sector, Satellite Industry, etc."
    #     " I am not interested in scientific discoveries related to space."
    # )
    newsletter_description_ = (
        "I want a newsletter about the conflict between Palestine and Israel."
    )
    asyncio.run(
        generate_newsletter(
            newsletter_description=newsletter_description_,
            user_id=0,
            email="petioptrv@icloud.com",
        )
    )
