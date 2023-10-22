from typing import Optional

import numpy as np
from pydantic import (
    EmailStr as PydanticEmailStr,
    AnyHttpUrl as PydanticAnyHttpUrl,
    HttpUrl as PydanticHttpUrl,
    PostgresDsn as PydanticPostgresDsn,
    BaseModel,
    ValidationError as PydanticValidationError,
    validator as pydantic_validator,
    BaseSettings,
    Field,
)


class Model(BaseModel):
    """Allows easy conversion to json-serializable dict."""

    def dict(self, *args, **kwargs):
        dict_ = super().dict(*args, **kwargs)
        return dict_


class NewsArticle(Model):
    title: str
    url: str
    image_url: Optional[str]
    newsletter_description: Optional[str]
    publishing_timestamp: int
    description: str
    content: str


class NewsArticleSearchResults(Model):
    total_results_count: int
    results: list[NewsArticle]


class NewsArticleSummary(Model):
    summary_title: str
    summary: str

    @property
    def is_initialized(self):
        return self.summary_title != "" and self.summary != ""


class NewsletterItem(Model):
    article: NewsArticle
    summary: NewsArticleSummary


class Newsletter(Model):
    content: str


class Embedding(Model):
    vector: np.ndarray
    model: str

    class Config:
        arbitrary_types_allowed = True


class CacheItem(Model):
    article: NewsArticle
    embedding: Embedding
    article_summary: NewsArticleSummary = Field(
        default=NewsArticleSummary(summary_title="", summary="")
    )

    @property
    def embedding_vector(self):
        return self.embedding.vector


class EmailStr(PydanticEmailStr):
    pass


class AnyHttpUrl(PydanticAnyHttpUrl):
    pass


class HttpUrl(PydanticHttpUrl):
    pass


class PostgresDsn(PydanticPostgresDsn):
    pass


class ValidationError(PydanticValidationError):
    pass


def validator(*args, **kwargs):
    return pydantic_validator(*args, **kwargs)


class Config(BaseSettings):
    pass
