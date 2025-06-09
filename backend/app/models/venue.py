from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..core.database import Base


class Venue(Base):
    __tablename__ = "venues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    address = Column(Text)
    city = Column(String(100), nullable=False, index=True)
    country = Column(String(100), default='Croatia')
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))
    capacity = Column(Integer)
    venue_type = Column(String(50))  # club, arena, outdoor, theater, etc.
    website = Column(String(500))
    phone = Column(String(50))
    email = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    events = relationship("Event", back_populates="venue")
    translations = relationship("VenueTranslation", back_populates="venue", cascade="all, delete-orphan")
    
    # Social relationships
    social_posts = relationship("SocialPost", back_populates="venue")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('name', 'city', name='_venue_name_city_uc'),
    )