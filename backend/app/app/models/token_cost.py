from sqlalchemy import Column, String, ForeignKey, PrimaryKeyConstraint, Integer

from app.db.base_class import Base


class TokenCost(Base):
    __tablename__ = "token_cost"

    issue_id = Column(String(32), ForeignKey("newsletter_issue.issue_id"))
    article_id = Column(String(32), ForeignKey("issue_article.article_id"))
    action = Column(String(32))
    input_tokens = Column(Integer)
    output_tokens = Column(Integer)

    __table_args__ = (PrimaryKeyConstraint("issue_id", "article_id", "action"),)
