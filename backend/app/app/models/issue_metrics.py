from typing import List, TYPE_CHECKING

from sqlalchemy import Column, String, ForeignKey, Integer, PrimaryKeyConstraint
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models import TokenCost


class IssueMetrics(Base):
    __tablename__ = "issue_metrics"

    issue_id = Column(String(32), ForeignKey("newsletter_issue.issue_id"))
    newsletter_generation_config_id = Column(
        Integer, ForeignKey("newsletter_generation_config.id")
    )
    time_to_generate = Column(Integer)
    token_costs: List["TokenCost"] = relationship("TokenCost")

    __table_args__ = (
        PrimaryKeyConstraint("issue_id", "newsletter_generation_config_id"),
    )
