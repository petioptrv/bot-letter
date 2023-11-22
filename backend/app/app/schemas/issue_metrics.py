from typing import List

from pydantic import BaseModel

from app.schemas import TokenCostCreate


class IssueMetricsBase(BaseModel):
    pass


class IssueMetricsCreate(IssueMetricsBase):
    issue_id: str
    newsletter_generation_config_id: int
    time_to_generate: int
    token_costs: List[TokenCostCreate] = []


class IssueMetricsUpdate(IssueMetricsBase):
    pass
