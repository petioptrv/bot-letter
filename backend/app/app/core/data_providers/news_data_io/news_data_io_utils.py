from enum import Enum

from pydantic import BaseSettings


class NewsDataIOConfig(BaseSettings):
    news_data_io_api_key: str


class NewsDataIOCategories(str, Enum):
    business = "business"
    entertainment = "entertainment"
    environment = "environment"
    food = "food"
    health = "health"
    politics = "politics"
    science = "science"
    sports = "sports"
    technology = "technology"
    top = "top"
    tourism = "tourism"
    world = "world"
