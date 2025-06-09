"""
Recurring events and event series models.
"""

import json
from datetime import date, datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class RecurrencePattern(Enum):
    """Recurrence pattern enumeration."""

    DAILY = "daily"
    WEEKLY = "weekly"
    BIWEEKLY = "biweekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class RecurrenceEndType(Enum):
    """How the recurrence should end."""

    NEVER = "never"
    AFTER_OCCURRENCES = "after_occurrences"
    ON_DATE = "on_date"


class SeriesStatus(Enum):
    """Event series status."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class EventInstanceStatus(Enum):
    """Individual event instance status."""

    SCHEDULED = "scheduled"
    PUBLISHED = "published"
    CANCELLED = "cancelled"
    COMPLETED = "completed"
    MODIFIED = "modified"


class EventSeries(Base):
    """Event series model for managing recurring events."""

    __tablename__ = "event_series"

    id = Column(Integer, primary_key=True, index=True)

    # Series metadata
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    category_id = Column(Integer, ForeignKey("event_categories.id"))
    venue_id = Column(Integer, ForeignKey("venues.id"))

    # Series configuration
    series_status = Column(SQLEnum(SeriesStatus), default=SeriesStatus.ACTIVE)
    is_template_based = Column(Boolean, default=True)  # Use template for instances
    auto_publish = Column(Boolean, default=False)  # Auto-publish instances
    advance_notice_days = Column(
        Integer, default=30
    )  # How far ahead to generate instances

    # Template event data (applied to all instances)
    template_title = Column(String(500))
    template_description = Column(Text)
    template_price = Column(String(100))
    template_image = Column(String(1000))
    template_tags = Column(JSON)
    template_metadata = Column(JSON)

    # Timing information
    start_date = Column(Date, nullable=False)
    start_time = Column(String(50))
    duration_minutes = Column(Integer)  # Event duration in minutes
    timezone = Column(String(50), default="Europe/Zagreb")

    # Recurrence configuration
    recurrence_pattern = Column(SQLEnum(RecurrencePattern), nullable=False)
    recurrence_interval = Column(Integer, default=1)  # e.g., every 2 weeks
    recurrence_end_type = Column(
        SQLEnum(RecurrenceEndType), default=RecurrenceEndType.NEVER
    )
    recurrence_end_date = Column(Date)
    max_occurrences = Column(Integer)

    # Custom recurrence rules (for complex patterns)
    custom_recurrence_rules = Column(JSON)  # RRULE-like specification
    excluded_dates = Column(JSON)  # Dates to skip
    included_dates = Column(JSON)  # Additional dates to include

    # Weekday specification for weekly/monthly patterns
    recurrence_days = Column(JSON)  # [1,3,5] for Monday, Wednesday, Friday

    # Statistics
    total_instances = Column(Integer, default=0)
    published_instances = Column(Integer, default=0)
    completed_instances = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    last_generated_at = Column(DateTime)

    # Relationships
    organizer = relationship("User")
    category = relationship("EventCategory")
    venue = relationship("Venue")
    instances = relationship(
        "EventInstance", back_populates="series", cascade="all, delete-orphan"
    )
    modifications = relationship(
        "SeriesModification", back_populates="series", cascade="all, delete-orphan"
    )


class EventInstance(Base):
    """Individual event instance within a series."""

    __tablename__ = "event_instances"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(
        Integer, ForeignKey("event_series.id", ondelete="CASCADE"), nullable=False
    )

    # Instance-specific data (can override series template)
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text)
    price = Column(String(100))
    image = Column(String(1000))
    location = Column(String(500))

    # Timing
    scheduled_date = Column(Date, nullable=False, index=True)
    scheduled_time = Column(String(50))
    duration_minutes = Column(Integer)
    timezone = Column(String(50))

    # Override flags
    title_overridden = Column(Boolean, default=False)
    description_overridden = Column(Boolean, default=False)
    price_overridden = Column(Boolean, default=False)
    image_overridden = Column(Boolean, default=False)
    location_overridden = Column(Boolean, default=False)
    time_overridden = Column(Boolean, default=False)

    # Instance metadata
    instance_status = Column(
        SQLEnum(EventInstanceStatus), default=EventInstanceStatus.SCHEDULED
    )
    sequence_number = Column(Integer, nullable=False)  # 1st, 2nd, 3rd occurrence
    is_exception = Column(Boolean, default=False)  # Manually added or moved

    # Linked actual event (when published)
    event_id = Column(Integer, ForeignKey("events.id"), unique=True)
    published_at = Column(DateTime)

    # Instance-specific metadata
    instance_notes = Column(Text)
    custom_metadata = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    series = relationship("EventSeries", back_populates="instances")
    event = relationship("Event")
    modifications = relationship(
        "InstanceModification", back_populates="instance", cascade="all, delete-orphan"
    )


class SeriesModification(Base):
    """Track modifications made to entire series."""

    __tablename__ = "series_modifications"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(
        Integer, ForeignKey("event_series.id", ondelete="CASCADE"), nullable=False
    )

    # Modification details
    modification_type = Column(
        String(50), nullable=False
    )  # schedule_change, template_update, etc.
    field_changed = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)

    # Application scope
    applies_to_future = Column(Boolean, default=True)  # Apply to future instances only
    applies_to_existing = Column(Boolean, default=False)  # Apply to existing instances
    affected_instance_ids = Column(JSON)  # Specific instances affected

    # Metadata
    reason = Column(Text)
    modified_by = Column(Integer, ForeignKey("users.id"))
    modification_metadata = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    applied_at = Column(DateTime)

    # Relationships
    series = relationship("EventSeries", back_populates="modifications")
    modifier = relationship("User")


class InstanceModification(Base):
    """Track modifications made to individual instances."""

    __tablename__ = "instance_modifications"

    id = Column(Integer, primary_key=True, index=True)
    instance_id = Column(
        Integer, ForeignKey("event_instances.id", ondelete="CASCADE"), nullable=False
    )

    # Modification details
    modification_type = Column(
        String(50), nullable=False
    )  # reschedule, cancel, content_change
    field_changed = Column(String(100))
    old_value = Column(Text)
    new_value = Column(Text)

    # Metadata
    reason = Column(Text)
    modified_by = Column(Integer, ForeignKey("users.id"))
    affects_future_instances = Column(Boolean, default=False)
    modification_metadata = Column(JSON)

    # Timestamps
    created_at = Column(DateTime, default=func.now())

    # Relationships
    instance = relationship("EventInstance", back_populates="modifications")
    modifier = relationship("User")


class RecurrenceRule(Base):
    """Complex recurrence rules for custom patterns."""

    __tablename__ = "recurrence_rules"

    id = Column(Integer, primary_key=True, index=True)
    series_id = Column(
        Integer, ForeignKey("event_series.id", ondelete="CASCADE"), nullable=False
    )

    # RRULE-like specification
    frequency = Column(String(20), nullable=False)  # DAILY, WEEKLY, MONTHLY, YEARLY
    interval = Column(Integer, default=1)
    count = Column(Integer)  # Number of occurrences
    until_date = Column(Date)  # End date

    # Day specifications
    by_weekday = Column(JSON)  # [0,1,2] for Monday, Tuesday, Wednesday (0=Monday)
    by_monthday = Column(JSON)  # [1,15] for 1st and 15th of month
    by_month = Column(JSON)  # [1,6,12] for January, June, December
    by_setpos = Column(JSON)  # [1,-1] for first and last occurrence

    # Week specifications
    week_start = Column(Integer, default=0)  # 0=Monday, 6=Sunday
    by_yearday = Column(JSON)  # Day of year
    by_weekno = Column(JSON)  # Week number

    # Time zone
    timezone = Column(String(50), default="Europe/Zagreb")

    # Metadata
    rule_name = Column(String(100))
    rule_description = Column(Text)
    custom_logic = Column(JSON)  # For very complex patterns

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    series = relationship("EventSeries")


class SeriesTemplate(Base):
    """Reusable templates for creating event series."""

    __tablename__ = "series_templates"

    id = Column(Integer, primary_key=True, index=True)

    # Template metadata
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    category = Column(String(100))  # e.g., "fitness", "education", "entertainment"

    # Template configuration
    default_recurrence_pattern = Column(SQLEnum(RecurrencePattern))
    default_recurrence_interval = Column(Integer, default=1)
    default_duration_minutes = Column(Integer)

    # Template content
    template_title_pattern = Column(
        String(500)
    )  # e.g., "Weekly Yoga Class #{sequence}"
    template_description = Column(Text)
    template_tags = Column(JSON)
    template_metadata = Column(JSON)

    # Suggested settings
    suggested_advance_notice_days = Column(Integer, default=30)
    suggested_auto_publish = Column(Boolean, default=False)

    # Usage statistics
    usage_count = Column(Integer, default=0)

    # Template flags
    is_public = Column(Boolean, default=True)
    is_system_template = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"))

    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    creator = relationship("User")


class EventInstanceView(Base):
    """Materialized view for optimized instance queries."""

    __tablename__ = "event_instance_view"

    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, index=True)

    # Computed fields for fast queries
    title = Column(String(500), index=True)
    scheduled_date = Column(Date, index=True)
    scheduled_time = Column(String(50))
    status = Column(String(50), index=True)

    # Series information
    series_title = Column(String(500))
    organizer_name = Column(String(255))
    category_name = Column(String(255))
    venue_name = Column(String(255))

    # Booking information
    has_tickets = Column(Boolean, default=False)
    tickets_available = Column(Integer)

    # Search optimization
    search_text = Column(Text)  # Pre-computed searchable text

    # Timestamps
    last_updated = Column(DateTime, default=func.now())

    # This is a view, so no relationships defined
