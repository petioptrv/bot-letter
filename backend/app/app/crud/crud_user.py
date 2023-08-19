import time
from typing import Any, Dict, Optional, Union, List

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import get_password_hash, verify_password
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.time_utils import timestamp_within_today


class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_all(self, db: Session) -> List[User]:
        return db.query(User).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        db_obj = User(
            email=obj_in.email,
            hashed_password=get_password_hash(obj_in.password),
            full_name=obj_in.full_name,
            is_superuser=obj_in.is_superuser,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)
        if update_data.get("password") is not None:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password
        return super().update(db, db_obj=db_obj, obj_in=update_data)

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

    def check_user_subscription_search_within_limits(self, *, db_object: User):
        within_limits = not timestamp_within_today(
            timestamp=db_object.last_subscription_search_timestamp,
            timezone=settings.TIMEZONE,
        ) or db_object.subscription_search_count < db_object.max_subscription_search_count
        return within_limits

    def increment_user_subscription_search_count(self, db: Session, *, db_object: User):
        update_data = {}

        if timestamp_within_today(
            timestamp=db_object.last_subscription_search_timestamp,
            timezone=settings.TIMEZONE,
        ):
            update_data["subscription_search_count"] = db_object.subscription_search_count + 1
        else:
            update_data["subscription_search_count"] = 1

        update_data["last_subscription_search_timestamp"] = time.time()

        return self.update(db, db_obj=db_object, obj_in=update_data)


user = CRUDUser(User)
