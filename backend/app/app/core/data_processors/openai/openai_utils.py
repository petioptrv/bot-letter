import asyncio
import logging
from enum import Enum
from typing import Optional

from app.base_types import Model, Config, Cost
from app.core.newsletter_creator.utils import log_for_newsletter_issue


class OpenAIConfig(Config):
    openai_api_key: str


openai_config = OpenAIConfig()


class OpenAIRoles(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class OpenAIChatCompletion(Model):
    role: OpenAIRoles
    content: str
    cost: Optional[Cost] = None

    def get_dict_for_api_request(self):
        return {
            "role": self.role.value,
            "content": self.content,
        }


class OpenAIModels(str, Enum):
    GPT_4_TURBO = "gpt-4-1106-preview"
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"


async def call_openai_api_with_rate_limit_protection(
    newsletter_issue_id: str, async_func: callable, *args, **kwargs
) -> any:
    result = None

    while result is None:
        try:
            result = await async_func(*args, **kwargs)
        except IOError as e:
            if "Rate limit reached" in str(e):
                log_for_newsletter_issue(
                    level=logging.WARNING,
                    issue_id=newsletter_issue_id,
                    message="Rate limit reached. Waiting 1 second.",
                )
                await asyncio.sleep(1)

    return result
