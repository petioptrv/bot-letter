from enum import Enum
from typing import Optional

from app.base_types import Model, Config, Cost


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
