from enum import Enum

from app.base_types import Config


class NewsDataIOConfig(Config):
    news_data_io_api_key: str


news_data_io_config = NewsDataIOConfig()


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
