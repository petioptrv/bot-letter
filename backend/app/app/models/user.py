from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .subscription import Subscription  # noqa: F401


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)
    subscriptions: List["Subscription"] = relationship("Subscription", back_populates="owner")
