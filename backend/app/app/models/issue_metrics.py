from typing import List

from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.models.token_cost import TokenCost


class IssueMetrics(Base):
    __tablename__ = "issue_metrics"

    metrics_id = Column(
        String(32), ForeignKey("newsletter_issue.issue_id"), primary_key=True
    )
    newsletter_generation_config_id = Column(
        Integer, ForeignKey("newsletter_generation_config.id"), nullable=False
    )
    time_to_generate = Column(Integer)
    token_costs: List[TokenCost] = relationship("TokenCost")
