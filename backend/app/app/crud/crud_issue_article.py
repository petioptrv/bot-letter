from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import IssueArticle
from app.schemas import IssueArticleCreate, IssueArticleUpdate


class CRUDIssueArticle(CRUDBase[IssueArticle, IssueArticleCreate, IssueArticleUpdate]):
    def create_issue_article(
        self, db: Session, *, obj_in: IssueArticleCreate
    ) -> IssueArticle:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


issue_article = CRUDIssueArticle(IssueArticle)
