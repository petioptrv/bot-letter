from sqlalchemy import Column, String, Text, PrimaryKeyConstraint, ForeignKey, Boolean

from app.db.base_class import Base


class RelevancyPrompt(Base):
    __tablename__ = "relevancy_prompt"

    issue_id = Column(String(32), ForeignKey("newsletter_issue.issue_id"))
    article_id = Column(String(36), nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("issue_id", "article_id"),
    )
