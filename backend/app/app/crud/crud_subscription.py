from typing import List

from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models import Subscription
from app.schemas.subscription import (
    SubscriptionCreate,
    SubscriptionUpdate,
    SubscriptionDelete,
)


class CRUDSubscription(CRUDBase[Subscription, SubscriptionCreate, SubscriptionUpdate]):
    def create_with_owner(
        self, db: Session, *, obj_in: SubscriptionCreate, owner_id: int
    ) -> Subscription:
        obj_in_data = jsonable_encoder(obj_in)
        db_obj = self.model(**obj_in_data, owner_id=owner_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_multi_by_owner(
        self, db: Session, *, owner_id: int, skip: int = 0, limit: int = 100
    ) -> List[Subscription]:
        return (
            db.query(self.model)
            .filter(Subscription.owner_id == owner_id)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def delete_by_owner(
        self, db: Session, *, obj_out: SubscriptionDelete, owner_id: int
    ) -> Subscription:
        item = (
            db.query(self.model)
            .filter(
                Subscription.owner_id == owner_id,
                Subscription.id == obj_out.id,
                # Subscription.search_term == obj_out.search_term,
            )
            .first()
        )
        db.delete(item)
        db.commit()
        return item


subscription = CRUDSubscription(Subscription)
