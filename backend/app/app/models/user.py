from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from ..core.config import settings

if TYPE_CHECKING:
    from .subscription import Subscription  # noqa: F401


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean(), default=True)
    last_subscription_search_timestamp = Column(Integer, default=0)
    subscription_search_count = Column(Integer, default=0)
    max_subscription_search_count = Column(Integer, default=settings.DEFAULT_MAX_SUBSCRIPTION_SEARCH_LIMIT)
    is_superuser = Column(Boolean(), default=False)
    subscriptions: List["Subscription"] = relationship("Subscription", back_populates="owner")
