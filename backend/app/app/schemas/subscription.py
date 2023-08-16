from typing import Optional

from app.base_types import Model


class SubscriptionBase(Model):
    search_term: Optional[str] = None


class SubscriptionCreate(SubscriptionBase):
    search_term: str


class SubscriptionUpdate(SubscriptionBase):
    pass


class SubscriptionDelete(SubscriptionBase):
    id: int
    search_term: str


class SubscriptionInDB(SubscriptionBase):
    id: int
    search_term: str
    owner_id: int

    class Config:
        orm_mode = True
