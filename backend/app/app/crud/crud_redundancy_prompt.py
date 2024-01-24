from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import RedundancyPrompt
from app.schemas import RedundancyPromptCreate, RedundancyPromptUpdate


class CRUDRedundancyPrompt(
    CRUDBase[RedundancyPrompt, RedundancyPromptCreate, RedundancyPromptUpdate]
):
    def create_redundancy_prompt(
        self, db: Session, *, obj_in: RedundancyPromptCreate
    ) -> RedundancyPrompt:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


redundancy_prompt = CRUDRedundancyPrompt(RedundancyPrompt)
