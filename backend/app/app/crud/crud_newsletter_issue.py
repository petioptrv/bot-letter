from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.newsletter_issue import NewsletterIssue
from app.schemas import NewsletterIssueCreate, NewsletterIssueUpdate


class CRUDNewsletterIssue(
    CRUDBase[
        NewsletterIssue,
        NewsletterIssueCreate,
        NewsletterIssueUpdate,
    ]
):
    def create_issue(
        self, db: Session, *, obj_in: NewsletterIssueCreate
    ) -> NewsletterIssue:
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data.pop("articles", None)
        obj_in_data.pop("metrics", None)
        obj_in_data.pop("relevancy_prompts", None)
        obj_in_data.pop("redundancy_prompts", None)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


newsletter_issue = CRUDNewsletterIssue(NewsletterIssue)
