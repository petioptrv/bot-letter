import logging
import time
from enum import Enum
from typing import List

from pydantic import BaseModel

from app.base_types import CacheItem
from app.cache.cache_base import CacheBase
from app.core.data_processors.openai.openai import OpenAI
from app.core.data_processors.openai.openai_utils import (
    OpenAIChatCompletion,
    OpenAIRoles,
    call_openai_api_with_rate_limit_protection,
)
from app.core.newsletter_creator.logging_utils import log_for_newsletter_issue
from app.core.newsletter_creator.newsletter_creator_utils import (
    newsletter_creator_config,
)
from app.schemas import NewsletterIssueCreate, TokenCostCreate


class Candidates(BaseModel):
    relevant_candidates: List[CacheItem] = []
    irrelevant_candidates: List[CacheItem] = []

    @property
    def candidate_titles(self) -> List[str]:
        return [
            candidate.article.title
            for candidate in self.relevant_candidates + self.irrelevant_candidates
        ]


class CreationAction(str, Enum):
    EMBEDDING = "embedding"
    RELEVANCY_CHECK = "relevancy_check"
    REDUNDANCY_CHECK = "redundancy_check"
    ALL_ARTICLES_QUALIFIER_CHECK = "all_articles_qualifier_check"
    SUMMARY = "summary"


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


def is_valid_candidate_item(
    newsletter_issue_id: str, item: CacheItem, candidate_titles: List[str]
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
            message=f"Article too short:\n\n{item.article.title}\n{item.article.description}",
        )
        valid = False

    title_already_included = item.article.title in candidate_titles if valid else False
    if valid and title_already_included:
        log_for_newsletter_issue(
            level=logging.INFO,
            issue_id=newsletter_issue_id,
            message=f"Article already included:\n\n{item.article.title}\n{item.article.description}",
        )
        valid = False

    return valid


async def get_article_selection_text(
    openai: OpenAI,
    cache: CacheBase,
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


async def ensure_article_is_summarized(
    openai: OpenAI,
    cache: CacheBase,
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
        summary_content = await call_openai_api_with_rate_limit_protection(
            newsletter_issue_id=newsletter_issue_id,
            async_func=openai.get_chat_completions,
            model=newsletter_creator_config.text_generation_model,
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
