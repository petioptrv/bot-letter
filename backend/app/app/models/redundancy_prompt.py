from sqlalchemy import Column, String, PrimaryKeyConstraint, ForeignKey, Boolean

from app.db.base_class import Base


class RedundancyPrompt(Base):
    __tablename__ = "redundancy_prompt"

    issue_id = Column(String(32), ForeignKey("newsletter_issue.issue_id"))
    current_article_id = Column(String(36), nullable=False)
    previous_article_id = Column(String(36), nullable=False)
    response = Column(Boolean, nullable=False)

    __table_args__ = (
        PrimaryKeyConstraint("issue_id", "current_article_id", "previous_article_id"),
    )
