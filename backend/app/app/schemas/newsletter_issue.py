from typing import List

from pydantic import BaseModel

from app.schemas.redundancy_prompt import RedundancyPromptCreate
from app.schemas.relevancy_prompt import RelevancyPromptCreate
from app.schemas.issue_article import IssueArticleCreate
from app.schemas.issue_metrics import IssueMetricsCreate


class NewsletterIssueBase(BaseModel):
    pass


class NewsletterIssueCreate(NewsletterIssueBase):
    issue_id: str
    subscription_id: int
    timestamp: int
    metrics: IssueMetricsCreate
    articles: List[IssueArticleCreate] = []
    relevancy_prompts: List[RelevancyPromptCreate] = []
    redundancy_prompts: List[RedundancyPromptCreate] = []


class NewsletterIssueUpdate(NewsletterIssueBase):
    pass
