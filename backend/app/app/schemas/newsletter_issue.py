from typing import List

from pydantic import BaseModel

from app.schemas import IssueArticleCreate, IssueMetricsCreate


class NewsletterIssueBase(BaseModel):
    pass


class NewsletterIssueCreate(NewsletterIssueBase):
    issue_id: str
    subscription_id: int
    timestamp: int
    articles: List[IssueArticleCreate]
    metrics: IssueMetricsCreate


class NewsletterIssueUpdate(NewsletterIssueBase):
    pass
