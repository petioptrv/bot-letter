import asyncio
import logging
import time
from itertools import chain, islice
from typing import Optional, List

from dotenv import load_dotenv
from pydantic import BaseModel

from app.base_types import NewsArticleSummary, NewsletterItem, CacheItem
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


class Candidates(BaseModel):
    relevant_candidates: List[CacheItem] = []
    irrelevant_candidates: List[CacheItem] = []

    @property
    def candidate_titles(self) -> List[str]:
        return [
            candidate.article.title
            for candidate in self.relevant_candidates + self.irrelevant_candidates
        ]


class NewsletterHTML(BaseModel):
    html: str
    newsletter_subject: str


async def generate_newsletter(newsletter_description: str, user_id: int, email: str):
    api_provider_ = APIProvider()
    openai = OpenAI(api_provider=api_provider_, config=openai_config)
    cache = AioRedisCache(config=redis_config)

    await cache.initialize()

    newsletter_generation_id = get_newsletter_generation_id(
        user_id=user_id, newsletter_description=newsletter_description
    )
    news_items = await get_news_items(
        cache=cache, newsletter_generation_id=newsletter_generation_id
    )
    candidates = await build_candidates(
        openai=openai,
        cache=cache,
        newsletter_description=newsletter_description,
        newsletter_generation_id=newsletter_generation_id,
        news_items=news_items,
    )
    newsletter_items = await build_newsletter_items(
        openai=openai,
        cache=cache,
        newsletter_generation_id=newsletter_generation_id,
        candidates=candidates,
    )

    if len(newsletter_items) != 0:
        html = await generate_html_for_non_empty_newsletter(
            api_provider_=api_provider_,
            openai=openai,
            newsletter_items=newsletter_items,
            newsletter_description=newsletter_description,
        )
    else:
        html = generate_html_for_empty_newsletter(
            newsletter_description=newsletter_description,
            newsletter_generation_id=newsletter_generation_id,
        )

    send_email(
        email_to=email,
        subject_template=html.newsletter_subject,
        html_template=html.html,
    )


def get_newsletter_generation_id(user_id: int, newsletter_description: str) -> str:
    newsletter_generation_id = f"{user_id}_{user_id}_{int(time.time())}"
    log_for_newsletter_generation(
        level=logging.INFO,
        generation_id=newsletter_generation_id,
        message=(
            f'Starting newsletter creation for search description "{newsletter_description}"'
            f"\nMax wordcount per article: {newsletter_creator_config.summary_max_word_count}"
        ),
    )
    return newsletter_generation_id


async def get_news_items(
    cache: AioRedisCache, newsletter_generation_id: str
) -> List[CacheItem]:
    since_timestamp = time.time() - settings.ARTICLES_FETCH_WINDOW

    log_for_newsletter_generation(
        level=logging.DEBUG,
        generation_id=newsletter_generation_id,
        message=f"Fetching new items since {since_timestamp}",
    )

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

    return news_items


async def build_candidates(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_description: str,
    newsletter_generation_id: str,
    news_items: List[CacheItem],
) -> Candidates:
    log_for_newsletter_generation(
        level=logging.DEBUG,
        generation_id=newsletter_generation_id,
        message=f"Building candidates from {len(news_items)} articles",
    )

    newsletter_description_embedding = await openai.get_embedding(
        model=OpenAIModels.TEXT_EMBEDDING_ADA_002, text=newsletter_description
    )

    processed_articles = 0
    candidates = Candidates()
    representative_items_generator = generate_most_representative_items(
        target_vector=newsletter_description_embedding.vector,
        cache_items=news_items,
    )

    async for item in representative_items_generator:
        if is_valid_candidate_item(
            newsletter_generation_id=newsletter_generation_id,
            item=item,
            candidates=candidates,
        ):
            await process_candidate_item(
                openai=openai,
                cache=cache,
                newsletter_description=newsletter_description,
                newsletter_generation_id=newsletter_generation_id,
                candidates=candidates,
                item=item,
            )
            processed_articles += 1
            if (
                processed_articles
                == newsletter_creator_config.max_processed_articles_per_newsletter
                or len(candidates.relevant_candidates)
                + len(candidates.irrelevant_candidates)
                == newsletter_creator_config.max_articles_per_newsletter
            ):
                break

    return candidates


def is_valid_candidate_item(
    newsletter_generation_id: str, item: CacheItem, candidates: Candidates
) -> bool:
    valid = True

    length_valid = (
        len(item.article.content) > newsletter_creator_config.summary_max_word_count
        if valid
        else False
    )
    if valid and not length_valid:
        log_for_newsletter_generation(
            level=logging.INFO,
            generation_id=newsletter_generation_id,
            message=f"Article too long:\n\n{item.article.title}\n{item.article.description}",
        )
        valid = False

    title_already_included = (
        item.article.title in candidates.candidate_titles if valid else False
    )
    if valid and title_already_included:
        log_for_newsletter_generation(
            level=logging.INFO,
            generation_id=newsletter_generation_id,
            message=f"Article already included:\n\n{item.article.title}\n{item.article.description}",
        )
        valid = False

    return valid


async def process_candidate_item(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_description: str,
    newsletter_generation_id: str,
    candidates: Candidates,
    item: CacheItem,
):
    log_for_newsletter_generation(
        level=logging.DEBUG,
        generation_id=newsletter_generation_id,
        message=f"Processing candidate item {item.article.title}.",
    )
    try:
        article_selection_text = await get_article_selection_text(
            openai=openai,
            cache=cache,
            newsletter_generation_id=newsletter_generation_id,
            item=item,
        )
        relevancy_prompt = newsletter_creator_config.article_relevancy_prompt.format(
            newsletter_description=newsletter_description,
            current_article_summary=article_selection_text,
        )
        relevancy_completion = OpenAIChatCompletion(
            role=OpenAIRoles.USER, content=relevancy_prompt
        )
        relevancy_response = await openai.get_chat_completions(
            model=OpenAIModels.GPT_4_TURBO,
            messages=[relevancy_completion],
        )
        if relevancy_response.content.lower() in ["no", "no."]:
            log_for_newsletter_generation(
                level=logging.INFO,
                generation_id=newsletter_generation_id,
                message=(
                    f"\nArticle not relevant:\n\n{item.article.title}\n{item.article.description}"
                ),
            )
            candidates.irrelevant_candidates.append(item)
        else:
            await process_relevant_candidate_item(
                openai=openai,
                cache=cache,
                newsletter_generation_id=newsletter_generation_id,
                candidates=candidates,
                item=item,
            )
    except IOError as e:
        if "Rate limit reached" in str(e):
            log_for_newsletter_generation(
                level=logging.WARNING,
                generation_id=newsletter_generation_id,
                message="Rate limit reached. Waiting 1 second.",
            )
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


async def process_relevant_candidate_item(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_generation_id: str,
    candidates: Candidates,
    item: CacheItem,
):
    log_for_newsletter_generation(
        level=logging.DEBUG,
        generation_id=newsletter_generation_id,
        message=f"Processing relevant candidate item {item.article.title}.",
    )
    include = True
    if len(candidates.relevant_candidates) != 0:
        for previous_newsletter_item in chain(
            candidates.relevant_candidates, candidates.irrelevant_candidates
        ):
            previous_article_selection_text = await get_article_selection_text(
                openai=openai,
                cache=cache,
                newsletter_generation_id=newsletter_generation_id,
                item=previous_newsletter_item,
            )
            current_article_selection_text = await get_article_selection_text(
                openai=openai,
                cache=cache,
                newsletter_generation_id=newsletter_generation_id,
                item=item,
            )
            redundancy_prompt = (
                newsletter_creator_config.article_redundancy_prompt.format(
                    previous_article_summary=previous_article_selection_text,
                    current_article_summary=current_article_selection_text,
                )
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
                log_for_newsletter_generation(
                    level=logging.INFO,
                    generation_id=newsletter_generation_id,
                    message=f"Article redundant:\n\n{item.article.title}\n{item.article.description}",
                )
                break
    if include:
        log_for_newsletter_generation(
            level=logging.DEBUG,
            generation_id=newsletter_generation_id,
            message=f"\nArticle relevant:\n\n{item.article.title}\n{item.article.description}",
        )
        candidates.relevant_candidates.append(item)


async def get_article_selection_text(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_generation_id: str,
    item: CacheItem,
) -> str:
    if (
        len(item.article.description)
        >= newsletter_creator_config.min_article_description_to_consider_for_article_evaluation_prompts_instead_of_article_summary
    ):
        article_selection_text = item.article.description
    else:
        await ensure_article_is_summarized(
            openai=openai,
            cache=cache,
            cache_item=item,
            newsletter_generation_id=newsletter_generation_id,
        )
        article_selection_text = item.article_summary.summary
    return article_selection_text


async def build_newsletter_items(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_generation_id: str,
    candidates: Candidates,
) -> List[NewsletterItem]:
    log_for_newsletter_generation(
        level=logging.DEBUG,
        generation_id=newsletter_generation_id,
        message=(
            f"Building newsletter items from {len(candidates.relevant_candidates)} relevant"
            f" and {len(candidates.irrelevant_candidates)} irrelevant articles"
        ),
    )

    newsletter_items = []

    for candidate in islice(
        chain(candidates.relevant_candidates, candidates.irrelevant_candidates),
        newsletter_creator_config.max_articles_per_newsletter,
    ):
        await ensure_article_is_summarized(
            openai=openai,
            cache=cache,
            cache_item=candidate,
            newsletter_generation_id=newsletter_generation_id,
        )
        newsletter_items.append(
            NewsletterItem(
                article=candidate.article,
                summary=NewsArticleSummary(
                    summary_title=candidate.article.title,
                    summary=candidate.article_summary.summary,
                ),
                relevant=candidate in candidates.relevant_candidates,
            )
        )

    return newsletter_items


async def ensure_article_is_summarized(
    openai: OpenAI,
    cache: AioRedisCache,
    cache_item: CacheItem,
    newsletter_generation_id: str,
):
    article_summary = cache_item.article_summary
    if not article_summary.is_initialized:
        article_summary_prompt = newsletter_creator_config.summary_prompt.format(
            word_count=newsletter_creator_config.summary_max_word_count,
        )
        article_summary_system_message = OpenAIChatCompletion(
            role=OpenAIRoles.SYSTEM, content=article_summary_prompt
        )
        summary_content = await openai.get_chat_completions(
            model=OpenAIModels.GPT_4_TURBO,
            messages=[
                article_summary_system_message,
                OpenAIChatCompletion(
                    role=OpenAIRoles.USER,
                    content=cache_item.article.content,
                ),
            ],
        )
        article_summary.summary_title = cache_item.article.title
        article_summary.summary = summary_content.content
        await cache.update_item(cache_item=cache_item)
        log_for_newsletter_generation(
            level=logging.DEBUG,
            generation_id=newsletter_generation_id,
            message=f"Summarized article {cache_item.article.title}",
        )


async def generate_html_for_non_empty_newsletter(
    api_provider_: APIProvider,
    openai: OpenAI,
    newsletter_items: List[NewsletterItem],
    newsletter_description: str,
) -> NewsletterHTML:
    none_relevant = all([not item.relevant for item in newsletter_items])
    newsletter_subject_prompt = (
        newsletter_creator_config.newsletter_subject_prompt.format(
            newsletter_content="\n\n".join(
                [
                    item.summary.summary
                    for item in newsletter_items
                    if item.relevant or none_relevant
                ]
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
        api_provider=api_provider_,
        newsletter_items=newsletter_items,
        newsletter_description=newsletter_description,
    )

    return NewsletterHTML(html=html, newsletter_subject=newsletter_subject)


def generate_html_for_empty_newsletter(
    newsletter_description: str, newsletter_generation_id: str
) -> NewsletterHTML:
    log_for_newsletter_generation(
        level=logging.WARNING,
        generation_id=newsletter_generation_id,
        message=f"No new articles found for search term {newsletter_description}",
    )
    newsletter_subject = "No new articles."
    newsletter_formatter = NewsletterFormatter()
    html = newsletter_formatter.format_newsletter_html_no_new_articles(
        newsletter_description=newsletter_description
    )

    return NewsletterHTML(html=html, newsletter_subject=newsletter_subject)


def log_for_newsletter_generation(
    level: int, generation_id: str, message: str, exc_info: Optional[Exception] = None
):
    logging.getLogger(__name__).log(
        level=level, msg=f"ng-{generation_id}: {message}", exc_info=exc_info
    )
