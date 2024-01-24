from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import RelevancyPrompt
from app.schemas import RelevancyPromptCreate, RelevancyPromptUpdate


class CRUDRelevancyPrompt(
    CRUDBase[RelevancyPrompt, RelevancyPromptCreate, RelevancyPromptUpdate]
):
    def create_relevancy_prompt(
        self, db: Session, *, obj_in: RelevancyPromptCreate
    ) -> RelevancyPrompt:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


relevancy_prompt = CRUDRelevancyPrompt(RelevancyPrompt)
