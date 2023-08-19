from typing import Optional, List

from app.base_types import EmailStr, Model
from app.schemas.subscription import SubscriptionBase, SubscriptionInDB


# Shared properties
class UserBase(Model):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    subscriptions: List[SubscriptionBase] = []


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    password: str


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None
    subscription_search_count: Optional[int] = None
    last_subscription_search_timestamp: Optional[int] = None


class UserInDBBase(UserBase):
    id: Optional[int] = None
    subscriptions: List[SubscriptionInDB] = []

    class Config:
        orm_mode = True


# Additional properties to return via API
class User(UserInDBBase):
    pass


# Additional properties stored in DB
class UserInDB(UserInDBBase):
    hashed_password: str
