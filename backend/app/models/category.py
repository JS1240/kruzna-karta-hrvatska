from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class EventCategory(Base):
    __tablename__ = "event_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    color = Column(String(7), default="#3B82F6")  # Hex color for UI
    icon = Column(String(50))  # Icon name for UI
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    events = relationship("Event", back_populates="category")
