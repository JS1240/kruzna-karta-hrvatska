from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)

    # Core event information
    title = Column(String(500), nullable=False, index=True)
    time = Column(String(50), nullable=False)
    date = Column(Date, nullable=False, index=True)
    price = Column(String(100))
    description = Column(Text)
    link = Column(String(1000))
    image = Column(String(1000))
    location = Column(String(500), nullable=False, index=True)

    # Enhanced fields for better functionality
    category_id = Column(Integer, ForeignKey("event_categories.id"), index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), index=True)

    # Geographic data for mapping
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))

    # Event metadata
    source = Column(String(50), nullable=False, default="manual", index=True)
    external_id = Column(String(255))
    event_status = Column(String(20), default="active", index=True)
    is_featured = Column(Boolean, default=False, index=True)
    is_recurring = Column(Boolean, default=False)

    # Additional event details
    organizer = Column(String(255))
    age_restriction = Column(String(50))
    ticket_info = Column(JSONB)  # Renamed to avoid conflict with relationship
    tags = Column(ARRAY(Text))

    # User-generated event fields
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    approval_status = Column(
        String(20), default="pending", index=True
    )  # pending, approved, rejected
    platform_commission_rate = Column(
        Numeric(5, 2), default=5.0
    )  # 5% default commission
    is_user_generated = Column(Boolean, default=False, index=True)

    # SEO and search
    slug = Column(String(600), unique=True)
    search_vector = Column(TSVECTOR)

    # Date/time management
    end_date = Column(Date)
    end_time = Column(String(50))
    timezone = Column(String(50), default="Europe/Zagreb")

    # Tracking and management
    view_count = Column(Integer, default=0)
    last_scraped_at = Column(DateTime(timezone=True))
    scrape_hash = Column(String(64))

    # Standard timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    category = relationship("EventCategory", back_populates="events")
    venue = relationship("Venue", back_populates="events")
    favorited_by = relationship(
        "User", secondary="user_favorites", back_populates="favorite_events"
    )
    translations = relationship(
        "EventTranslation", back_populates="event", cascade="all, delete-orphan"
    )
    ticket_types = relationship(
        "TicketType", back_populates="event", cascade="all, delete-orphan"
    )
    bookings = relationship("Booking", back_populates="event")
    instance = relationship("EventInstance", back_populates="event", uselist=False)

    # Social relationships
    social_posts = relationship("SocialPost", back_populates="event")
    reviews = relationship(
        "EventReview", back_populates="event", cascade="all, delete-orphan"
    )
    attendances = relationship(
        "EventAttendance", back_populates="event", cascade="all, delete-orphan"
    )
    notifications = relationship("SocialNotification", back_populates="event")

    # User-generated event relationships
    event_organizer = relationship(
        "User", foreign_keys=[organizer_id], back_populates="organized_events"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "date >= CURRENT_DATE - INTERVAL '1 year'", name="events_date_check"
        ),
        CheckConstraint(
            "end_date IS NULL OR end_date >= date", name="events_end_date_check"
        ),
        CheckConstraint(
            "event_status IN ('active', 'cancelled', 'postponed', 'sold_out', 'draft')",
            name="events_status_check",
        ),
        CheckConstraint(
            "source IN ('entrio', 'croatia', 'manual', 'api', 'facebook', 'eventbrite', 'user_generated')",
            name="events_source_check",
        ),
        CheckConstraint(
            "approval_status IN ('pending', 'approved', 'rejected')",
            name="events_approval_check",
        ),
    )
