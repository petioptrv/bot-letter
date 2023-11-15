from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.db.base_class import Base

if TYPE_CHECKING:
    from .user import User  # noqa: F401


class Subscription(Base):
    id = Column(Integer, primary_key=True, index=True)
    newsletter_description = Column(String)
    sample_available = Column(Boolean, default=True)
    owner_id = Column(Integer, ForeignKey("user.id"))
    owner = relationship("User", back_populates="subscriptions")
