import asyncio
import logging
from itertools import chain
from typing import AsyncGenerator

from app.base_types import CacheItem
from app.cache.cache_base import CacheBase
from app.core.data_processors.openai.openai import OpenAI
from app.core.data_processors.openai.openai_utils import (
    OpenAIChatCompletion,
    OpenAIRoles,
    OpenAIModels,
)
from app.core.newsletter_creator.newsletter_creator_utils import NewsletterCreatorConfig
from app.core.newsletter_creator.utils import (
    Candidates,
    is_valid_candidate_item,
    get_article_selection_text,
    CreationAction,
)
from app.core.newsletter_creator.logging_utils import log_for_newsletter_issue
from app.schemas import NewsletterIssueCreate, TokenCostCreate, IssueArticleCreate, RelevancyPromptCreate, \
    RedundancyPromptCreate


async def granular_candidate_selection(
    newsletter_creator_config: NewsletterCreatorConfig,
    newsletter_issue_id: str,
    newsletter_description: str,
    openai: OpenAI,
    cache: CacheBase,
    representative_items_generator: AsyncGenerator[CacheItem, None],
    in_issue: NewsletterIssueCreate,
) -> Candidates:
    processed_articles = 0
    candidates = Candidates()

    async for item in representative_items_generator:
        if is_valid_candidate_item(
            newsletter_issue_id=newsletter_issue_id,
            item=item,
            candidate_titles=candidates.candidate_titles,
        ):
            await process_candidate_item(
                newsletter_creator_config=newsletter_creator_config,
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


async def process_candidate_item(
    newsletter_creator_config: NewsletterCreatorConfig,
    openai: OpenAI,
    cache: CacheBase,
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

        if relevancy_response.content.lower() in ["no", "no.", "No", "No."]:
            log_for_newsletter_issue(
                level=logging.INFO,
                issue_id=newsletter_issue_id,
                message=(
                    f"\nArticle not relevant:\n\n{item.article.title}\n{item.article.description}"
                ),
            )
            in_issue.relevancy_prompts.append(
                RelevancyPromptCreate(
                    issue_id=newsletter_issue_id,
                    article_id=item.article.article_id,
                    response=False,
                )
            )
            candidates.irrelevant_candidates.append(item)
            in_issue.articles.append(
                IssueArticleCreate(
                    issue_id=newsletter_issue_id,
                    article_id=item.article.article_id,
                )
            )
        else:
            in_issue.relevancy_prompts.append(
                RelevancyPromptCreate(
                    issue_id=newsletter_issue_id,
                    article_id=item.article.article_id,
                    response=True,
                )
            )
            await process_relevant_candidate_item(
                newsletter_creator_config=newsletter_creator_config,
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
    newsletter_creator_config: NewsletterCreatorConfig,
    openai: OpenAI,
    cache: CacheBase,
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
                in_issue.redundancy_prompts.append(
                    RedundancyPromptCreate(
                        issue_id=newsletter_issue_id,
                        article_id=item.article.article_id,
                        response=True,
                    )
                )
                include = False
                log_for_newsletter_issue(
                    level=logging.INFO,
                    issue_id=newsletter_issue_id,
                    message=f"Article redundant:\n\n{item.article.title}\n{item.article.description}",
                )
                break
            else:
                in_issue.redundancy_prompts.append(
                    RedundancyPromptCreate(
                        issue_id=newsletter_issue_id,
                        current_article_id=item.article.article_id,
                        previous_article_id=previous_newsletter_item.article.article_id,
                        response=False,
                    )
                )
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
