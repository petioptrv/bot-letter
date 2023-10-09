from enum import Enum

from app.base_types import Model, Config


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


class OpenAIModels(str, Enum):
    GPT_4 = "gpt-4"
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"
