from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
)

from app.db.base_class import Base


class TokenCost(Base):
    __tablename__ = "token_cost"

    token_cost_id = Column(Integer, primary_key=True, index=True)
    metrics_id = Column(String(32), ForeignKey("issue_metrics.metrics_id"), nullable=False)
    article_id = Column(String(36))
    action = Column(String(32))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)
