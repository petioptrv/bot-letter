from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKeyConstraint,
    ForeignKey,
)

from app.db.base_class import Base


class TokenCost(Base):
    __tablename__ = "token_cost"

    token_cost_id = Column(Integer, primary_key=True, index=True)
    metrics_id = Column(String(32), ForeignKey("issue_metrics.metrics_id"), nullable=False)
    issue_id = Column(String(32), nullable=False)
    article_id = Column(String(36), nullable=False)
    action = Column(String(32), nullable=False)
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)

    __table_args__ = (
        ForeignKeyConstraint(
            ["issue_id", "article_id"],
            ["issue_article.issue_id", "issue_article.article_id"],
        ),
    )
