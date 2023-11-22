from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import IssueMetrics
from app.schemas import IssueMetricsCreate, IssueMetricsUpdate


class CRUDIssueMetrics(CRUDBase[IssueMetrics, IssueMetricsCreate, IssueMetricsUpdate]):
    def create_issue_metrics(
        self, db: Session, *, obj_in: IssueMetricsCreate
    ) -> IssueMetrics:
        obj_in_data = jsonable_encoder(obj_in)
        obj_in_data.pop("token_costs", None)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


issue_metrics = CRUDIssueMetrics(IssueMetrics)
