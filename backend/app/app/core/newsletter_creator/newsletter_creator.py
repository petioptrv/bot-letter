import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
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
from app.db.session import SessionLocal
from app.schemas import (
    NewsletterIssueCreate,
    IssueMetricsCreate,
    TokenCostCreate,
    IssueArticleCreate,
)
from app.utils import send_email
from app import crud

load_dotenv()


class CreationAction(str, Enum):
    EMBEDDING = "embedding"
    RELEVANCY_CHECK = "relevancy_check"
    REDUNDANCY_CHECK = "redundancy_check"
    SUMMARY = "summary"


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


def get_newsletter_issue_id(
    user_id: int, subscription_id: int, newsletter_description: str
) -> str:
    newsletter_issue_id = f"{user_id}-{subscription_id}-{int(time.time())}"
    log_for_newsletter_issue(
        level=logging.INFO,
        issue_id=newsletter_issue_id,
        message=(
            f'Starting newsletter creation for search description "{newsletter_description}"'
            f"\nMax wordcount per article: {newsletter_creator_config.summary_max_word_count}"
        ),
    )
    return newsletter_issue_id


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

    newsletter_description_embedding = await openai.get_embedding(
        model=OpenAIModels.TEXT_EMBEDDING_ADA_002, text=newsletter_description
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
    processed_articles = 0
    candidates = Candidates()
    representative_items_generator = generate_most_representative_items(
        target_vector=newsletter_description_embedding.vector,
        cache_items=news_items,
    )

    async for item in representative_items_generator:
        if is_valid_candidate_item(
            newsletter_issue_id=newsletter_issue_id,
            item=item,
            candidates=candidates,
        ):
            await process_candidate_item(
                openai=openai,
                cache=cache,
                newsletter_description=newsletter_description,
                newsletter_issue_id=newsletter_issue_id,
                candidates=candidates,
                item=item,
                in_issue=in_issue,
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
    newsletter_issue_id: str, item: CacheItem, candidates: Candidates
) -> bool:
    valid = True

    length_valid = (
        len(item.article.content) > newsletter_creator_config.summary_max_word_count
        if valid
        else False
    )
    if valid and not length_valid:
        log_for_newsletter_issue(
            level=logging.INFO,
            issue_id=newsletter_issue_id,
            message=f"Article too long:\n\n{item.article.title}\n{item.article.description}",
        )
        valid = False

    title_already_included = (
        item.article.title in candidates.candidate_titles if valid else False
    )
    if valid and title_already_included:
        log_for_newsletter_issue(
            level=logging.INFO,
            issue_id=newsletter_issue_id,
            message=f"Article already included:\n\n{item.article.title}\n{item.article.description}",
        )
        valid = False

    return valid


async def process_candidate_item(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_description: str,
    newsletter_issue_id: str,
    candidates: Candidates,
    item: CacheItem,
    in_issue: NewsletterIssueCreate,
):
    log_for_newsletter_issue(
        level=logging.DEBUG,
        issue_id=newsletter_issue_id,
        message=f"Processing candidate item {item.article.title}.",
    )
    try:
        article_selection_text = await get_article_selection_text(
            openai=openai,
            cache=cache,
            newsletter_issue_id=newsletter_issue_id,
            item=item,
            in_issue=in_issue,
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
        in_issue.metrics.token_costs.append(
            TokenCostCreate(
                metrics_id=newsletter_issue_id,
                article_id=item.article.article_id,
                action=CreationAction.RELEVANCY_CHECK,
                input_tokens=relevancy_response.cost.input_tokens,
                output_tokens=relevancy_response.cost.output_tokens,
            )
        )

        if relevancy_response.content.lower() in ["no", "no."]:
            log_for_newsletter_issue(
                level=logging.INFO,
                issue_id=newsletter_issue_id,
                message=(
                    f"\nArticle not relevant:\n\n{item.article.title}\n{item.article.description}"
                ),
            )
            candidates.irrelevant_candidates.append(item)
            in_issue.articles.append(
                IssueArticleCreate(
                    issue_id=newsletter_issue_id,
                    article_id=item.article.article_id,
                )
            )
        else:
            await process_relevant_candidate_item(
                openai=openai,
                cache=cache,
                newsletter_issue_id=newsletter_issue_id,
                candidates=candidates,
                item=item,
                in_issue=in_issue,
            )
    except IOError as e:
        if "Rate limit reached" in str(e):
            log_for_newsletter_issue(
                level=logging.WARNING,
                issue_id=newsletter_issue_id,
                message="Rate limit reached. Waiting 1 second.",
            )
            await asyncio.sleep(1)
        else:
            log_for_newsletter_issue(
                level=logging.ERROR,
                issue_id=newsletter_issue_id,
                message=f"Failed to parse summary for article {item.article}",
                exc_info=e,
            )
    except Exception as e:
        log_for_newsletter_issue(
            level=logging.ERROR,
            issue_id=newsletter_issue_id,
            message=f"Failed to parse summary for article {item.article}",
            exc_info=e,
        )


async def process_relevant_candidate_item(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_issue_id: str,
    candidates: Candidates,
    item: CacheItem,
    in_issue: NewsletterIssueCreate,
):
    log_for_newsletter_issue(
        level=logging.DEBUG,
        issue_id=newsletter_issue_id,
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
                newsletter_issue_id=newsletter_issue_id,
                item=previous_newsletter_item,
                in_issue=in_issue,
            )
            current_article_selection_text = await get_article_selection_text(
                openai=openai,
                cache=cache,
                newsletter_issue_id=newsletter_issue_id,
                item=item,
                in_issue=in_issue,
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
            in_issue.metrics.token_costs.append(
                TokenCostCreate(
                    metrics_id=newsletter_issue_id,
                    article_id=item.article.article_id,
                    action=CreationAction.REDUNDANCY_CHECK,
                    input_tokens=redundancy_response.cost.input_tokens,
                    output_tokens=redundancy_response.cost.output_tokens,
                )
            )
            if redundancy_response.content.lower() in ["yes", "yes."]:
                include = False
                log_for_newsletter_issue(
                    level=logging.INFO,
                    issue_id=newsletter_issue_id,
                    message=f"Article redundant:\n\n{item.article.title}\n{item.article.description}",
                )
                break
    if include:
        log_for_newsletter_issue(
            level=logging.DEBUG,
            issue_id=newsletter_issue_id,
            message=f"\nArticle relevant:\n\n{item.article.title}\n{item.article.description}",
        )
        candidates.relevant_candidates.append(item)
        in_issue.articles.append(
            IssueArticleCreate(
                issue_id=newsletter_issue_id,
                article_id=item.article.article_id,
            )
        )


async def get_article_selection_text(
    openai: OpenAI,
    cache: AioRedisCache,
    newsletter_issue_id: str,
    item: CacheItem,
    in_issue: NewsletterIssueCreate,
) -> str:
    if (
        len(item.article.description)
        >= newsletter_creator_config.min_description_len_for_evaluation_prompts
    ):
        article_selection_text = item.article.description
    else:
        await ensure_article_is_summarized(
            openai=openai,
            cache=cache,
            cache_item=item,
            newsletter_issue_id=newsletter_issue_id,
            in_issue=in_issue,
        )
        article_selection_text = item.article_summary.summary
    return article_selection_text


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


async def ensure_article_is_summarized(
    openai: OpenAI,
    cache: AioRedisCache,
    cache_item: CacheItem,
    newsletter_issue_id: str,
    in_issue: NewsletterIssueCreate,
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
        in_issue.metrics.token_costs.append(
            TokenCostCreate(
                metrics_id=newsletter_issue_id,
                article_id=cache_item.article.article_id,
                action=CreationAction.SUMMARY,
                input_tokens=summary_content.cost.input_tokens,
                output_tokens=summary_content.cost.output_tokens,
            )
        )
        article_summary.summary_title = cache_item.article.title
        article_summary.summary = summary_content.content
        await cache.update_item(cache_item=cache_item)
        log_for_newsletter_issue(
            level=logging.DEBUG,
            issue_id=newsletter_issue_id,
            message=f"Summarized article {cache_item.article.title}",
        )


async def generate_html_for_non_empty_newsletter(
    api_provider_: APIProvider,
    openai: OpenAI,
    newsletter_items: List[NewsletterItem],
    newsletter_issue_id: str,
    newsletter_description: str,
    in_issue: NewsletterIssueCreate,
) -> NewsletterHTML:
    none_relevant = all([not item.relevant for item in newsletter_items])
    # newsletter_subject_prompt = (
    #     newsletter_creator_config.newsletter_subject_prompt.format(
    #         newsletter_content="\n\n".join(
    #             [
    #                 item.summary.summary
    #                 for item in newsletter_items
    #                 if item.relevant or none_relevant
    #             ]
    #         )
    #     )
    # )
    # subject_completion = OpenAIChatCompletion(
    #     role=OpenAIRoles.USER, content=newsletter_subject_prompt
    # )
    # subject_response = await openai.get_chat_completions(
    #     model=OpenAIModels.GPT_4_TURBO, messages=[subject_completion]
    # )
    # in_issue.metrics.token_costs.append(
    #     TokenCostCreate(
    #         metrics_id=newsletter_issue_id,
    #         article_id="nw-subject",
    #         action=CreationAction.SUMMARY,
    #         input_tokens=subject_response.cost.input_tokens,
    #         output_tokens=subject_response.cost.output_tokens,
    #     )
    # )
    # newsletter_subject = subject_response.content
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
        crud.issue_article.create_issue_article(
            db=db_session, obj_in=in_article
        )
    crud.issue_metrics.create_issue_metrics(db=db_session, obj_in=in_issue.metrics)
    for in_cost in in_issue.metrics.token_costs:
        crud.token_cost.create_token_cost(db=db_session, obj_in=in_cost)


def log_for_newsletter_issue(
    level: int, issue_id: str, message: str, exc_info: Optional[Exception] = None
):
    logging.getLogger(__name__).log(
        level=level, msg=f"ni-{issue_id}: {message}", exc_info=exc_info
    )


if __name__ == "__main__":
    asyncio.run(
        generate_newsletter(
            newsletter_description="I want news about the Gaza Strip war. I am interested in peace resolution attempts.",
            user_id=1,
            subscription_id=11,
            email="botletternews@gmail.com",
        )
    )
