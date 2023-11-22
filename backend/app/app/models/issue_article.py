from sqlalchemy import Column, String, ForeignKey, PrimaryKeyConstraint, Integer

from app.db.base_class import Base


class IssueArticle(Base):
    __tablename__ = "issue_article"

    issue_id = Column(String(32), ForeignKey("newsletter_issue.issue_id"))
    article_id = Column(String(36), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("issue_id", "article_id"),)
