from typing import Optional

from app.base_types import Model


class SubscriptionBase(Model):
    newsletter_description: Optional[str] = None


class SubscriptionCreate(SubscriptionBase):
    newsletter_description: str


class SubscriptionIssue(SubscriptionBase):
    id: int
    newsletter_description: str


class SubscriptionUpdate(SubscriptionBase):
    pass


class SubscriptionDelete(SubscriptionBase):
    id: int
    newsletter_description: str


class SubscriptionInDB(SubscriptionBase):
    id: int
    newsletter_description: str
    owner_id: int

    class Config:
        orm_mode = True
