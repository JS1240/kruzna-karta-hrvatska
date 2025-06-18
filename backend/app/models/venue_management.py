from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class VenueStatus(PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    PERMANENTLY_CLOSED = "permanently_closed"


class FacilityType(PyEnum):
    ACCESSIBILITY = "accessibility"
    AUDIO_VISUAL = "audio_visual"
    CATERING = "catering"
    PARKING = "parking"
    SECURITY = "security"
    UTILITIES = "utilities"
    AMENITIES = "amenities"


class AvailabilityStatus(PyEnum):
    AVAILABLE = "available"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"


class BookingStatus(PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# Association table for venue facilities (many-to-many)
venue_facilities = Table(
    "venue_facilities",
    Base.metadata,
    Column(
        "venue_id",
        Integer,
        ForeignKey("enhanced_venues.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "facility_id",
        Integer,
        ForeignKey("facilities.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("notes", Text),
    Column("is_included", Boolean, default=True),
    Column("additional_cost", Numeric(10, 2)),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class EnhancedVenue(Base):
    """Enhanced venue model with comprehensive management features"""

    __tablename__ = "enhanced_venues"

    id = Column(Integer, primary_key=True, index=True)

    # Basic venue information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(300), unique=True)
    description = Column(Text)
    address = Column(Text)
    city = Column(String(100), nullable=False, index=True)
    postal_code = Column(String(20))
    country = Column(String(100), default="Croatia")
    region = Column(String(100))  # Croatian counties

    # Geographic data
    latitude = Column(Numeric(10, 8))
    longitude = Column(Numeric(11, 8))

    # Venue specifications
    capacity = Column(Integer)
    max_capacity = Column(Integer)
    min_capacity = Column(Integer)
    venue_type = Column(String(50), index=True)
    venue_status = Column(SQLEnum(VenueStatus), default=VenueStatus.ACTIVE, index=True)

    # Contact information
    website = Column(String(500))
    phone = Column(String(50))
    email = Column(String(255))
    contact_person = Column(String(255))
    emergency_contact = Column(String(50))

    # Business details
    tax_id = Column(String(50))
    registration_number = Column(String(50))
    business_hours = Column(JSONB)  # Store opening hours

    # Venue features
    floor_plan = Column(Text)  # URL to floor plan image
    virtual_tour_url = Column(String(500))
    photos = Column(ARRAY(Text))  # Array of photo URLs
    videos = Column(ARRAY(Text))  # Array of video URLs

    # Pricing and policies
    base_price_per_hour = Column(Numeric(10, 2))
    base_price_per_day = Column(Numeric(10, 2))
    security_deposit = Column(Numeric(10, 2))
    cleaning_fee = Column(Numeric(10, 2))
    cancellation_policy = Column(Text)
    payment_terms = Column(Text)

    # Operational details
    setup_time_minutes = Column(Integer, default=60)
    breakdown_time_minutes = Column(Integer, default=60)
    minimum_booking_hours = Column(Integer, default=2)
    maximum_booking_days = Column(Integer, default=30)
    advance_booking_days = Column(Integer, default=90)

    # Technical specifications
    technical_specs = Column(JSONB)  # Audio, lighting, staging details
    accessibility_features = Column(JSONB)
    safety_certifications = Column(ARRAY(String))

    # Management info
    owner_id = Column(Integer, ForeignKey("users.id"), index=True)
    manager_id = Column(Integer, ForeignKey("users.id"), index=True)
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime(timezone=True))

    # Statistics
    total_bookings = Column(Integer, default=0)
    total_revenue = Column(Numeric(12, 2), default=0)
    average_rating = Column(Numeric(3, 2))
    total_reviews = Column(Integer, default=0)

    # SEO and search
    search_keywords = Column(ARRAY(String))
    meta_description = Column(String(300))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    last_booking_at = Column(DateTime(timezone=True))

    # Relationships
    owner = relationship("User", foreign_keys=[owner_id], back_populates="owned_venues")
    manager = relationship(
        "User", foreign_keys=[manager_id], back_populates="managed_venues"
    )
    facilities = relationship(
        "Facility", secondary=venue_facilities, back_populates="venues"
    )
    availability_slots = relationship(
        "VenueAvailability", back_populates="venue", cascade="all, delete-orphan"
    )
    bookings = relationship("VenueBooking", back_populates="venue")
    reviews = relationship(
        "VenueReview", back_populates="venue", cascade="all, delete-orphan"
    )
    images = relationship(
        "VenueImage", back_populates="venue", cascade="all, delete-orphan"
    )
    pricing_rules = relationship(
        "VenuePricingRule", back_populates="venue", cascade="all, delete-orphan"
    )
    maintenance_logs = relationship(
        "VenueMaintenanceLog", back_populates="venue", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("max_capacity >= capacity", name="venue_capacity_check"),
        CheckConstraint("min_capacity <= capacity", name="venue_min_capacity_check"),
        CheckConstraint("base_price_per_hour >= 0", name="venue_hourly_price_check"),
        CheckConstraint("base_price_per_day >= 0", name="venue_daily_price_check"),
        CheckConstraint(
            "average_rating >= 0 AND average_rating <= 5", name="venue_rating_check"
        ),
        UniqueConstraint("slug", name="venue_slug_unique"),
    )


class Facility(Base):
    """Venue facilities and amenities"""

    __tablename__ = "facilities"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(Text)
    facility_type = Column(SQLEnum(FacilityType), nullable=False, index=True)
    icon = Column(String(50))  # Icon class or emoji
    is_essential = Column(Boolean, default=False)  # Required for venue operation
    default_cost = Column(Numeric(10, 2), default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    venues = relationship(
        "EnhancedVenue", secondary=venue_facilities, back_populates="facilities"
    )


class VenueAvailability(Base):
    """Venue availability calendar"""

    __tablename__ = "venue_availability"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(
        Integer,
        ForeignKey("enhanced_venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Time slots
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)

    # Availability details
    status = Column(
        SQLEnum(AvailabilityStatus), default=AvailabilityStatus.AVAILABLE, index=True
    )
    capacity_override = Column(Integer)  # Override venue capacity for this slot
    price_override = Column(Numeric(10, 2))  # Override base price

    # Booking information
    booking_id = Column(Integer, ForeignKey("venue_bookings.id"), index=True)
    blocked_reason = Column(String(500))
    notes = Column(Text)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    venue = relationship("EnhancedVenue", back_populates="availability_slots")
    booking = relationship("VenueBooking", back_populates="availability_slots")

    # Constraints
    __table_args__ = (
        CheckConstraint("end_time > start_time", name="availability_time_check"),
        UniqueConstraint(
            "venue_id", "start_time", "end_time", name="venue_availability_unique"
        ),
    )


class VenueBooking(Base):
    """Venue booking management"""

    __tablename__ = "venue_bookings"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(
        Integer,
        ForeignKey("enhanced_venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id = Column(Integer, ForeignKey("users.id"), index=True)

    # Event details
    event_name = Column(String(500), nullable=False)
    event_type = Column(String(100))
    event_description = Column(Text)
    expected_attendance = Column(Integer)

    # Booking details
    booking_reference = Column(String(50), unique=True, nullable=False)
    booking_status = Column(
        SQLEnum(BookingStatus), default=BookingStatus.PENDING, index=True
    )

    # Time details
    start_datetime = Column(DateTime(timezone=True), nullable=False, index=True)
    end_datetime = Column(DateTime(timezone=True), nullable=False)
    setup_start = Column(DateTime(timezone=True))
    breakdown_end = Column(DateTime(timezone=True))

    # Pricing
    base_cost = Column(Numeric(10, 2), nullable=False)
    facility_costs = Column(Numeric(10, 2), default=0)
    additional_costs = Column(Numeric(10, 2), default=0)
    discount_amount = Column(Numeric(10, 2), default=0)
    tax_amount = Column(Numeric(10, 2), default=0)
    total_cost = Column(Numeric(10, 2), nullable=False)

    # Payment details
    deposit_amount = Column(Numeric(10, 2))
    deposit_paid_at = Column(DateTime(timezone=True))
    payment_due_date = Column(DateTime(timezone=True))
    payment_completed_at = Column(DateTime(timezone=True))

    # Contact details
    contact_name = Column(String(255), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(50))

    # Special requirements
    special_requirements = Column(Text)
    catering_requirements = Column(Text)
    av_requirements = Column(Text)
    accessibility_requirements = Column(Text)

    # Insurance and liability
    insurance_certificate = Column(String(500))  # URL to certificate
    liability_acknowledged = Column(Boolean, default=False)

    # Status tracking
    confirmed_at = Column(DateTime(timezone=True))
    cancelled_at = Column(DateTime(timezone=True))
    cancellation_reason = Column(Text)
    completed_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    venue = relationship("EnhancedVenue", back_populates="bookings")
    customer = relationship("User", back_populates="venue_bookings")
    availability_slots = relationship("VenueAvailability", back_populates="booking")
    payments = relationship(
        "VenuePayment", back_populates="booking", cascade="all, delete-orphan"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("end_datetime > start_datetime", name="booking_time_check"),
        CheckConstraint("total_cost >= 0", name="booking_cost_check"),
        CheckConstraint("expected_attendance >= 0", name="booking_attendance_check"),
    )


class VenuePayment(Base):
    """Venue booking payment tracking"""

    __tablename__ = "venue_payments"

    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(
        Integer,
        ForeignKey("venue_bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    payment_type = Column(String(50), nullable=False)  # deposit, final, refund
    payment_method = Column(String(50))  # card, bank_transfer, cash
    payment_status = Column(String(50), default="pending")

    # External payment data
    transaction_id = Column(String(255))
    payment_processor = Column(String(50))
    payment_reference = Column(String(255))

    # Timestamps
    due_date = Column(DateTime(timezone=True))
    paid_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    booking = relationship("VenueBooking", back_populates="payments")


class VenueReview(Base):
    """Venue reviews and ratings"""

    __tablename__ = "venue_reviews"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(
        Integer,
        ForeignKey("enhanced_venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    booking_id = Column(Integer, ForeignKey("venue_bookings.id"), index=True)

    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200))
    review_text = Column(Text)

    # Detailed ratings
    cleanliness_rating = Column(Integer)
    staff_rating = Column(Integer)
    facilities_rating = Column(Integer)
    value_rating = Column(Integer)
    location_rating = Column(Integer)

    # Metadata
    is_verified = Column(Boolean, default=False)  # Based on actual booking
    is_public = Column(Boolean, default=True)
    helpful_votes = Column(Integer, default=0)

    # Response from venue
    venue_response = Column(Text)
    venue_responded_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    venue = relationship("EnhancedVenue", back_populates="reviews")
    user = relationship("User", back_populates="venue_reviews")
    booking = relationship("VenueBooking")

    # Constraints
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="review_rating_check"),
        CheckConstraint(
            "cleanliness_rating IS NULL OR (cleanliness_rating >= 1 AND cleanliness_rating <= 5)",
            name="cleanliness_rating_check",
        ),
        CheckConstraint(
            "staff_rating IS NULL OR (staff_rating >= 1 AND staff_rating <= 5)",
            name="staff_rating_check",
        ),
        CheckConstraint(
            "facilities_rating IS NULL OR (facilities_rating >= 1 AND facilities_rating <= 5)",
            name="facilities_rating_check",
        ),
        CheckConstraint(
            "value_rating IS NULL OR (value_rating >= 1 AND value_rating <= 5)",
            name="value_rating_check",
        ),
        CheckConstraint(
            "location_rating IS NULL OR (location_rating >= 1 AND location_rating <= 5)",
            name="location_rating_check",
        ),
        UniqueConstraint(
            "venue_id", "user_id", "booking_id", name="unique_venue_review"
        ),
    )


class VenueImage(Base):
    """Venue image management"""

    __tablename__ = "venue_images"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(
        Integer,
        ForeignKey("enhanced_venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Image details
    url = Column(String(1000), nullable=False)
    filename = Column(String(255))
    title = Column(String(200))
    description = Column(Text)
    alt_text = Column(String(200))

    # Image metadata
    image_type = Column(String(50))  # exterior, interior, facility, event
    is_primary = Column(Boolean, default=False)
    display_order = Column(Integer, default=0)

    # Technical details
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    mime_type = Column(String(50))

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    venue = relationship("EnhancedVenue", back_populates="images")


class VenuePricingRule(Base):
    """Dynamic pricing rules for venues"""

    __tablename__ = "venue_pricing_rules"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(
        Integer,
        ForeignKey("enhanced_venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Rule details
    name = Column(String(200), nullable=False)
    description = Column(Text)
    rule_type = Column(
        String(50), nullable=False
    )  # seasonal, day_of_week, duration, capacity

    # Conditions
    conditions = Column(JSONB, nullable=False)  # Flexible condition storage

    # Pricing adjustments
    price_adjustment_type = Column(
        String(20), nullable=False
    )  # percentage, fixed_amount
    price_adjustment_value = Column(Numeric(10, 2), nullable=False)

    # Validity
    valid_from = Column(DateTime(timezone=True))
    valid_to = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority rules apply first

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    venue = relationship("EnhancedVenue", back_populates="pricing_rules")


class VenueMaintenanceLog(Base):
    """Venue maintenance and service records"""

    __tablename__ = "venue_maintenance_logs"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(
        Integer,
        ForeignKey("enhanced_venues.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Maintenance details
    maintenance_type = Column(String(100), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)

    # Scheduling
    scheduled_date = Column(DateTime(timezone=True))
    completed_date = Column(DateTime(timezone=True))
    estimated_duration_hours = Column(Integer)
    actual_duration_hours = Column(Integer)

    # Personnel
    assigned_to = Column(String(255))
    contractor_company = Column(String(255))
    contact_person = Column(String(255))

    # Status and impact
    status = Column(
        String(50), default="scheduled"
    )  # scheduled, in_progress, completed, cancelled
    affects_availability = Column(Boolean, default=True)
    affected_areas = Column(ARRAY(String))

    # Costs
    estimated_cost = Column(Numeric(10, 2))
    actual_cost = Column(Numeric(10, 2))
    invoice_number = Column(String(100))

    # Documentation
    before_photos = Column(ARRAY(String))
    after_photos = Column(ARRAY(String))
    documentation_urls = Column(ARRAY(String))
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    venue = relationship("EnhancedVenue", back_populates="maintenance_logs")
