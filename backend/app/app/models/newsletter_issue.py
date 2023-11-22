from typing import List, TYPE_CHECKING

from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from app.models import IssueArticle


class NewsletterIssue(Base):
    __tablename__ = "newsletter_issue"

    issue_id = Column(String(32), primary_key=True, index=True)
    subscription_id = Column(
        Integer, ForeignKey("subscription.id"), nullable=False
    )
    timestamp = Column(Integer, nullable=False)
    articles: List["IssueArticle"] = relationship("IssueArticle")
    metrics = relationship("IssueMetrics")
