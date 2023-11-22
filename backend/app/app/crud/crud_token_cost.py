from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import TokenCost
from app.schemas import TokenCostCreate, TokenCostUpdate


class CRUDTokenCost(CRUDBase[TokenCost, TokenCostCreate, TokenCostUpdate]):
    def create_token_cost(self, db: Session, *, obj_in: TokenCostCreate) -> TokenCost:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


token_cost = CRUDTokenCost(TokenCost)
