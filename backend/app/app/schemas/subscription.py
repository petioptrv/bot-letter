from typing import Optional

from app.base_types import Model


class SubscriptionBase(Model):
    search_term: Optional[str] = None


class SubscriptionBaseInDBBase(SubscriptionBase):
    id: int
    search_term: str
    owner_id: int

    class Config:
        orm_mode = True
