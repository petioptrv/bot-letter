from typing import List

from app.base_types import Model
from app.schemas.token_cost import TokenCostCreate


class IssueMetricsBase(Model):
    pass


class IssueMetricsCreate(IssueMetricsBase):
    issue_id: str
    newsletter_generation_config_id: int
    time_to_generate: int
    token_costs: List[TokenCostCreate] = []


class IssueMetricsUpdate(IssueMetricsBase):
    pass
