from enum import Enum

from pydantic import BaseSettings, BaseModel


class OpenAIConfig(BaseSettings):
    openai_api_key: str


class OpenAIRoles(str, Enum):
    SYSTEM = "system"
    USER = "user"


class OpenAIChatCompletion(BaseModel):
    role: OpenAIRoles
    content: str


class OpenAIModels(str, Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    TEXT_EMBEDDING_ADA_002 = "text-embedding-ada-002"
