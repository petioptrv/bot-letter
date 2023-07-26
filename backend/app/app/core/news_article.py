from dataclasses import dataclass


@dataclass
class NewsArticle:
    title: str
    url: str
    image_url: str
    search_term: str
    publishing_timestamp: int
    content: str
