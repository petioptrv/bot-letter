import asyncio
import logging
import time
from datetime import datetime
from itertools import chain, islice
from typing import List

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
    openai_config, call_openai_api_with_rate_limit_protection,
)
from app.core.newsletter_creator.coarse_candidate_selection import coarse_candidate_selection
from app.core.newsletter_creator.granular_candidate_selection import granular_candidate_selection
from app.core.newsletter_creator.newsletter_creator_utils import (
    newsletter_creator_config,
)
from app.core.newsletter_creator.utils import log_for_newsletter_issue, Candidates, CreationAction, \
    ensure_article_is_summarized, get_newsletter_issue_id
from app.core.newsletter_formatter import NewsletterFormatter
from app.core.selection_algos.representative_items_algo import (
    generate_most_representative_items,
)
from app.db.session import SessionLocal
from app.schemas import (
    NewsletterIssueCreate,
    IssueMetricsCreate,
    TokenCostCreate,
)
from app.utils import send_email
from app import crud

load_dotenv()


class NewsletterHTML(BaseModel):
    html: str
    newsletter_subject: str


async def generate_newsletter(
    newsletter_description: str, user_id: int, subscription_id: int, email: str
):
    newsletter_issue_start_time = time.time()

    api_provider_ = APIProvider()
    openai = OpenAI(api_provider=api_provider_, config=openai_config)
    cache = AioRedisCache(config=redis_config)

    await cache.initialize()

    newsletter_issue_id = get_newsletter_issue_id(
        user_id=user_id,
        subscription_id=subscription_id,
        newsletter_description=newsletter_description,
    )
    in_metrics = IssueMetricsCreate(
        metrics_id=newsletter_issue_id,
        newsletter_generation_config_id=newsletter_creator_config.version,
        time_to_generate=-1,
    )
    in_issue = NewsletterIssueCreate(
        issue_id=newsletter_issue_id,
        subscription_id=subscription_id,
        timestamp=int(newsletter_issue_start_time),
        metrics=in_metrics,
    )
    news_items = await get_news_items(
        cache=cache, newsletter_issue_id=newsletter_issue_id
    )
    candidates = await build_candidates(
        openai=openai,
        cache=cache,
        newsletter_description=newsletter_description,
        newsletter_issue_id=newsletter_issue_id,
        news_items=news_items,
        in_issue=in_issue,
    )
    newsletter_items = await build_newsletter_items(
        openai=openai,
        cache=cache,
        newsletter_issue_id=newsletter_issue_id,
        candidates=candidates,
        in_issue=in_issue,
    )

    if len(newsletter_items) != 0:
        html = await generate_html_for_non_empty_newsletter(
            api_provider_=api_provider_,
            openai=openai,
            newsletter_items=newsletter_items,
            newsletter_issue_id=newsletter_issue_id,
            newsletter_description=newsletter_description,
            in_issue=in_issue,
        )
    else:
        html = generate_html_for_empty_newsletter(
            newsletter_description=newsletter_description,
            newsletter_issue_id=newsletter_issue_id,
        )

    send_email(
        email_to=email,
        subject_template=html.newsletter_subject,
        html_template=html.html,
    )
    in_metrics.time_to_generate = int(time.time() - newsletter_issue_start_time)
    log_issue_to_db(in_issue=in_issue)


async def get_news_items(
    cache: AioRedisCache, newsletter_issue_id: str
) -> List[CacheItem]:
    since_timestamp = time.time() - settings.ARTICLES_FETCH_WINDOW

    log_for_newsletter_issue(
        level=logging.DEBUG,
        issue_id=newsletter_issue_id,
        message=f"Fetching new items since {since_timestamp}",
    )

    news_items = await cache.get_items_since(
        newsletter_description=None, since_timestamp=since_timestamp
    )

    if len(news_items) == 0:
        new_items_log_level = logging.WARNING
    else:
        new_items_log_level = logging.DEBUG
    log_for_newsletter_issue(
        level=new_items_log_level,
        issue_id=newsletter_issue_id,
        message=f"Retrieved {len(news_items)} new items since {since_timestamp}",
    )

    return news_items


async def build_candidates(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_description: str,
    newsletter_issue_id: str,
    news_items: List[CacheItem],
    in_issue: NewsletterIssueCreate,
) -> Candidates:
    log_for_newsletter_issue(
        level=logging.DEBUG,
        issue_id=newsletter_issue_id,
        message=f"Building candidates from {len(news_items)} articles",
    )

    newsletter_description_embedding = await call_openai_api_with_rate_limit_protection(
        newsletter_issue_id=newsletter_issue_id,
        async_func=openai.get_embedding,
        model=OpenAIModels.TEXT_EMBEDDING_ADA_002,
        text=newsletter_description,
    )
    in_issue.metrics.token_costs.append(
        TokenCostCreate(
            metrics_id=newsletter_issue_id,
            article_id="nw-description",
            action=CreationAction.EMBEDDING,
            input_tokens=newsletter_description_embedding.cost.input_tokens,
            output_tokens=newsletter_description_embedding.cost.output_tokens,
        )
    )
    representative_items_generator = generate_most_representative_items(
        target_vector=newsletter_description_embedding.vector,
        cache_items=news_items,
    )

    candidates = await granular_candidate_selection(
        newsletter_creator_config=newsletter_creator_config,
        newsletter_issue_id=newsletter_issue_id,
        newsletter_description=newsletter_description,
        openai=openai,
        cache=cache,
        representative_items_generator=representative_items_generator,
        in_issue=in_issue,
    )

    return candidates


async def build_newsletter_items(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_issue_id: str,
    candidates: Candidates,
    in_issue: NewsletterIssueCreate,
) -> List[NewsletterItem]:
    log_for_newsletter_issue(
        level=logging.DEBUG,
        issue_id=newsletter_issue_id,
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
            newsletter_issue_id=newsletter_issue_id,
            in_issue=in_issue,
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


async def generate_html_for_non_empty_newsletter(
    api_provider_: APIProvider,
    openai: OpenAI,
    newsletter_items: List[NewsletterItem],
    newsletter_issue_id: str,
    newsletter_description: str,
    in_issue: NewsletterIssueCreate,
) -> NewsletterHTML:
    newsletter_subject = f'"{newsletter_description}" - {datetime.utcnow().strftime(settings.NEWSLETTER_ISSUE_DATE_FORMAT)}'

    newsletter_formatter = NewsletterFormatter()
    html = await newsletter_formatter.format_newsletter_html(
        api_provider=api_provider_,
        newsletter_items=newsletter_items,
        newsletter_description=newsletter_description,
    )

    return NewsletterHTML(html=html, newsletter_subject=newsletter_subject)


def generate_html_for_empty_newsletter(
    newsletter_description: str, newsletter_issue_id: str
) -> NewsletterHTML:
    log_for_newsletter_issue(
        level=logging.WARNING,
        issue_id=newsletter_issue_id,
        message=f"No new articles found for search term {newsletter_description}",
    )
    newsletter_subject = f'"{newsletter_description}" - {datetime.utcnow().strftime(settings.NEWSLETTER_ISSUE_DATE_FORMAT)}'
    newsletter_formatter = NewsletterFormatter()
    html = newsletter_formatter.format_newsletter_html_no_new_articles(
        newsletter_description=newsletter_description
    )

    return NewsletterHTML(html=html, newsletter_subject=newsletter_subject)


def log_issue_to_db(in_issue: NewsletterIssueCreate):
    db_session = SessionLocal()

    crud.newsletter_issue.create_issue(db=db_session, obj_in=in_issue)
    for in_article in in_issue.articles:
        crud.issue_article.create_issue_article(db=db_session, obj_in=in_article)
    for in_relevancy_prompt in in_issue.relevancy_prompts:
        crud.relevancy_prompt.create_relevancy_prompt(
            db=db_session, obj_in=in_relevancy_prompt
        )
    for in_redundancy_prompt in in_issue.redundancy_prompts:
        crud.redundancy_prompt.create_redundancy_prompt(
            db=db_session, obj_in=in_redundancy_prompt
        )
    crud.issue_metrics.create_issue_metrics(db=db_session, obj_in=in_issue.metrics)
    for in_cost in in_issue.metrics.token_costs:
        crud.token_cost.create_token_cost(db=db_session, obj_in=in_cost)


if __name__ == "__main__":
    from app.schemas import SubscriptionCreate

    newsletter_description_ = (
        "I want a newsletter about the video game industry."
        " I am interested in the business and venture capital side of the industry."
    )
    user_id_ = 1
    db_session_ = SessionLocal()

    subscription = crud.subscription.get_by_owner_and_description(
        db=db_session_, owner_id=user_id_, newsletter_description=newsletter_description_
    )
    if subscription is None:
        subscription = crud.subscription.create_with_owner(
            db=db_session_,
            obj_in=SubscriptionCreate(newsletter_description=newsletter_description_),
            owner_id=user_id_,
        )

    subscription_id = subscription.id

    asyncio.run(
        generate_newsletter(
            newsletter_description=newsletter_description_,
            user_id=user_id_,
            subscription_id=subscription_id,
            email="botletternews@gmail.com",
        )
    )
