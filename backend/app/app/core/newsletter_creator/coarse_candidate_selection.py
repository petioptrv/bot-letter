import json
import logging
from typing import AsyncGenerator, List

from app.base_types import CacheItem
from app.cache.cache_base import CacheBase
from app.core.data_processors.openai.openai import OpenAI
from app.core.data_processors.openai.openai_utils import (
    OpenAIChatCompletion,
    OpenAIRoles,
    call_openai_api_with_rate_limit_protection,
)
from app.core.newsletter_creator.newsletter_creator_utils import NewsletterCreatorConfig
from app.core.newsletter_creator.utils import (
    is_valid_candidate_item,
    get_article_selection_text,
    Candidates, CreationAction,
)
from app.core.newsletter_creator.logging_utils import log_for_newsletter_issue
from app.schemas import IssueArticleCreate, NewsletterIssueCreate, TokenCostCreate


async def coarse_candidate_selection(
    newsletter_creator_config: NewsletterCreatorConfig,
    newsletter_issue_id: str,
    newsletter_description: str,
    openai: OpenAI,
    cache: CacheBase,
    representative_items_generator: AsyncGenerator[CacheItem, None],
    in_issue: NewsletterIssueCreate,
) -> Candidates:
    # todo: add prompt logging for model fine-tuning

    validated_candidate_items = []
    async for item in representative_items_generator:
        if is_valid_candidate_item(
            newsletter_issue_id=newsletter_issue_id,
            item=item,
            candidate_titles=[ci.article.title for ci in validated_candidate_items],
        ):
            validated_candidate_items.append(item)
            if (
                len(validated_candidate_items)
                == newsletter_creator_config.max_processed_articles_per_newsletter
            ):
                break

    candidates = await select_candidates(
        newsletter_creator_config=newsletter_creator_config,
        openai=openai,
        cache=cache,
        newsletter_description=newsletter_description,
        newsletter_issue_id=newsletter_issue_id,
        validated_candidate_items=validated_candidate_items,
        in_issue=in_issue,
    )

    return candidates


async def select_candidates(
    newsletter_creator_config: NewsletterCreatorConfig,
    openai: OpenAI,
    cache: CacheBase,
    newsletter_description: str,
    newsletter_issue_id: str,
    validated_candidate_items: List[CacheItem],
    in_issue: NewsletterIssueCreate,
) -> Candidates:
    articles_selection_prompt = (
        newsletter_creator_config.articles_qualifier_prompt.format(
            newsletter_description=newsletter_description,
            articles_count=len(validated_candidate_items),
        )
    )
    for i, item in enumerate(validated_candidate_items):
        article_selection_text = await get_article_selection_text(
            openai=openai,
            cache=cache,
            newsletter_issue_id=newsletter_issue_id,
            item=item,
            in_issue=in_issue,
        )
        articles_selection_prompt += (
            f"\n\nArticle {i + 1}:" f"\n\n{article_selection_text}"
        )

    articles_selection_system_message = OpenAIChatCompletion(
        role=OpenAIRoles.SYSTEM, content=articles_selection_prompt
    )
    article_selection_response = await call_openai_api_with_rate_limit_protection(
        newsletter_issue_id=newsletter_issue_id,
        async_func=openai.get_chat_completions,
        model=newsletter_creator_config.decision_model,
        messages=[
            articles_selection_system_message,
            OpenAIChatCompletion(
                role=OpenAIRoles.USER,
                content="",
            ),
        ],
    )
    in_issue.metrics.token_costs.append(
        TokenCostCreate(
            metrics_id=newsletter_issue_id,
            article_id="nw-selection",
            action=CreationAction.ALL_ARTICLES_QUALIFIER_CHECK,
            input_tokens=article_selection_response.cost.input_tokens,
            output_tokens=article_selection_response.cost.output_tokens,
        )
    )
    try:
        article_selection = json.loads(
            article_selection_response.content.removeprefix("```json\n").removesuffix(
                "\n```"
            )
        )
    except json.JSONDecodeError as e:
        log_for_newsletter_issue(
            level=logging.ERROR,
            issue_id=newsletter_issue_id,
            message=f"Failed to parse article selection response: {article_selection_response.content}",
            exc_info=e,
        )
        article_selection = {"include": [], "redundant": []}

    redundant_map = {
        duplicate: redundant_list[0]
        for redundant_list in article_selection["redundant"]
        for duplicate in redundant_list[1:]
    }
    candidates = Candidates()
    for i, item in enumerate(validated_candidate_items):
        if i + 1 in redundant_map:
            continue
        in_issue.articles.append(
            IssueArticleCreate(
                issue_id=newsletter_issue_id,
                article_id=item.article.article_id,
            )
        )
        if i + 1 in article_selection["include"]:
            candidates.relevant_candidates.append(item)
        else:
            candidates.irrelevant_candidates.append(item)

    return candidates
