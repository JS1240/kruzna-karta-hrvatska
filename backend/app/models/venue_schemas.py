from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class VenueStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    PERMANENTLY_CLOSED = "permanently_closed"


class FacilityType(str, Enum):
    ACCESSIBILITY = "accessibility"
    AUDIO_VISUAL = "audio_visual"
    CATERING = "catering"
    PARKING = "parking"
    SECURITY = "security"
    UTILITIES = "utilities"
    AMENITIES = "amenities"


class AvailabilityStatus(str, Enum):
    AVAILABLE = "available"
    BOOKED = "booked"
    MAINTENANCE = "maintenance"
    BLOCKED = "blocked"


class BookingStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


# Facility Schemas
class FacilityBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    facility_type: FacilityType
    icon: Optional[str] = Field(None, max_length=50)
    is_essential: bool = False
    default_cost: Optional[Decimal] = Field(default=0, ge=0)


class FacilityCreate(FacilityBase):
    pass


class FacilityUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    facility_type: Optional[FacilityType] = None
    icon: Optional[str] = Field(None, max_length=50)
    is_essential: Optional[bool] = None
    default_cost: Optional[Decimal] = Field(None, ge=0)


class Facility(FacilityBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Venue Facility Association
class VenueFacilityBase(BaseModel):
    facility_id: int
    notes: Optional[str] = None
    is_included: bool = True
    additional_cost: Optional[Decimal] = Field(default=0, ge=0)


class VenueFacilityCreate(VenueFacilityBase):
    pass


class VenueFacility(VenueFacilityBase):
    facility: Facility
    created_at: datetime

    class Config:
        from_attributes = True


# Enhanced Venue Schemas
class EnhancedVenueBase(BaseModel):
    name: str = Field(..., max_length=255)
    description: Optional[str] = None
    address: Optional[str] = None
    city: str = Field(..., max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: str = Field(default="Croatia", max_length=100)
    region: Optional[str] = Field(None, max_length=100)

    # Geographic data
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    # Venue specifications
    capacity: Optional[int] = Field(None, ge=1)
    max_capacity: Optional[int] = Field(None, ge=1)
    min_capacity: Optional[int] = Field(None, ge=1)
    venue_type: Optional[str] = Field(None, max_length=50)
    venue_status: VenueStatus = VenueStatus.ACTIVE

    # Contact information
    website: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    emergency_contact: Optional[str] = Field(None, max_length=50)

    # Business details
    tax_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=50)
    business_hours: Optional[Dict[str, Any]] = None

    # Venue features
    floor_plan: Optional[str] = None
    virtual_tour_url: Optional[str] = Field(None, max_length=500)
    photos: Optional[List[str]] = None
    videos: Optional[List[str]] = None

    # Pricing and policies
    base_price_per_hour: Optional[Decimal] = Field(None, ge=0)
    base_price_per_day: Optional[Decimal] = Field(None, ge=0)
    security_deposit: Optional[Decimal] = Field(None, ge=0)
    cleaning_fee: Optional[Decimal] = Field(None, ge=0)
    cancellation_policy: Optional[str] = None
    payment_terms: Optional[str] = None

    # Operational details
    setup_time_minutes: int = Field(default=60, ge=0)
    breakdown_time_minutes: int = Field(default=60, ge=0)
    minimum_booking_hours: int = Field(default=2, ge=1)
    maximum_booking_days: int = Field(default=30, ge=1)
    advance_booking_days: int = Field(default=90, ge=0)

    # Technical specifications
    technical_specs: Optional[Dict[str, Any]] = None
    accessibility_features: Optional[Dict[str, Any]] = None
    safety_certifications: Optional[List[str]] = None

    # SEO and search
    search_keywords: Optional[List[str]] = None
    meta_description: Optional[str] = Field(None, max_length=300)

    @field_validator("max_capacity")
    @classmethod
    def validate_max_capacity(cls, v, info):
        if v is not None and "capacity" in info.data and info.data.get("capacity") is not None:
            if v < info.data.get("capacity"):
                raise ValueError(
                    "max_capacity must be greater than or equal to capacity"
                )
        return v

    @field_validator("min_capacity")
    @classmethod
    def validate_min_capacity(cls, v, info):
        if v is not None and "capacity" in info.data and info.data.get("capacity") is not None:
            if v > info.data.get("capacity"):
                raise ValueError("min_capacity must be less than or equal to capacity")
        return v


class EnhancedVenueCreate(EnhancedVenueBase):
    pass


class EnhancedVenueUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    postal_code: Optional[str] = Field(None, max_length=20)
    country: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=100)

    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None

    capacity: Optional[int] = Field(None, ge=1)
    max_capacity: Optional[int] = Field(None, ge=1)
    min_capacity: Optional[int] = Field(None, ge=1)
    venue_type: Optional[str] = Field(None, max_length=50)
    venue_status: Optional[VenueStatus] = None

    website: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)
    contact_person: Optional[str] = Field(None, max_length=255)
    emergency_contact: Optional[str] = Field(None, max_length=50)

    tax_id: Optional[str] = Field(None, max_length=50)
    registration_number: Optional[str] = Field(None, max_length=50)
    business_hours: Optional[Dict[str, Any]] = None

    floor_plan: Optional[str] = None
    virtual_tour_url: Optional[str] = Field(None, max_length=500)
    photos: Optional[List[str]] = None
    videos: Optional[List[str]] = None

    base_price_per_hour: Optional[Decimal] = Field(None, ge=0)
    base_price_per_day: Optional[Decimal] = Field(None, ge=0)
    security_deposit: Optional[Decimal] = Field(None, ge=0)
    cleaning_fee: Optional[Decimal] = Field(None, ge=0)
    cancellation_policy: Optional[str] = None
    payment_terms: Optional[str] = None

    setup_time_minutes: Optional[int] = Field(None, ge=0)
    breakdown_time_minutes: Optional[int] = Field(None, ge=0)
    minimum_booking_hours: Optional[int] = Field(None, ge=1)
    maximum_booking_days: Optional[int] = Field(None, ge=1)
    advance_booking_days: Optional[int] = Field(None, ge=0)

    technical_specs: Optional[Dict[str, Any]] = None
    accessibility_features: Optional[Dict[str, Any]] = None
    safety_certifications: Optional[List[str]] = None

    search_keywords: Optional[List[str]] = None
    meta_description: Optional[str] = Field(None, max_length=300)


class EnhancedVenue(EnhancedVenueBase):
    id: int
    slug: Optional[str] = None
    owner_id: Optional[int] = None
    manager_id: Optional[int] = None
    is_verified: bool = False
    verification_date: Optional[datetime] = None

    # Statistics
    total_bookings: int = 0
    total_revenue: Optional[Decimal] = 0
    average_rating: Optional[Decimal] = None
    total_reviews: int = 0

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_booking_at: Optional[datetime] = None

    # Relationships (when needed)
    facilities: Optional[List[VenueFacility]] = None

    class Config:
        from_attributes = True


# Availability Schemas
class VenueAvailabilityBase(BaseModel):
    date: datetime
    start_time: datetime
    end_time: datetime
    status: AvailabilityStatus = AvailabilityStatus.AVAILABLE
    capacity_override: Optional[int] = Field(None, ge=1)
    price_override: Optional[Decimal] = Field(None, ge=0)
    blocked_reason: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v, info):
        if "start_time" in info.data and v <= info.data.get("start_time"):
            raise ValueError("end_time must be after start_time")
        return v


class VenueAvailabilityCreate(VenueAvailabilityBase):
    venue_id: int


class VenueAvailabilityUpdate(BaseModel):
    date: Optional[datetime] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[AvailabilityStatus] = None
    capacity_override: Optional[int] = Field(None, ge=1)
    price_override: Optional[Decimal] = Field(None, ge=0)
    blocked_reason: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = None


class VenueAvailability(VenueAvailabilityBase):
    id: int
    venue_id: int
    booking_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Booking Schemas
class VenueBookingBase(BaseModel):
    event_name: str = Field(..., max_length=500)
    event_type: Optional[str] = Field(None, max_length=100)
    event_description: Optional[str] = None
    expected_attendance: Optional[int] = Field(None, ge=1)

    start_datetime: datetime
    end_datetime: datetime
    setup_start: Optional[datetime] = None
    breakdown_end: Optional[datetime] = None

    contact_name: str = Field(..., max_length=255)
    contact_email: str = Field(..., max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)

    special_requirements: Optional[str] = None
    catering_requirements: Optional[str] = None
    av_requirements: Optional[str] = None
    accessibility_requirements: Optional[str] = None

    insurance_certificate: Optional[str] = Field(None, max_length=500)
    liability_acknowledged: bool = False

    @field_validator("end_datetime")
    @classmethod
    def validate_end_datetime(cls, v, info):
        if "start_datetime" in info.data and v <= info.data.get("start_datetime"):
            raise ValueError("end_datetime must be after start_datetime")
        return v


class VenueBookingCreate(VenueBookingBase):
    venue_id: int


class VenueBookingUpdate(BaseModel):
    event_name: Optional[str] = Field(None, max_length=500)
    event_type: Optional[str] = Field(None, max_length=100)
    event_description: Optional[str] = None
    expected_attendance: Optional[int] = Field(None, ge=1)

    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    setup_start: Optional[datetime] = None
    breakdown_end: Optional[datetime] = None

    contact_name: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[str] = Field(None, max_length=255)
    contact_phone: Optional[str] = Field(None, max_length=50)

    special_requirements: Optional[str] = None
    catering_requirements: Optional[str] = None
    av_requirements: Optional[str] = None
    accessibility_requirements: Optional[str] = None

    insurance_certificate: Optional[str] = Field(None, max_length=500)
    liability_acknowledged: Optional[bool] = None

    booking_status: Optional[BookingStatus] = None
    cancellation_reason: Optional[str] = None


class VenueBooking(VenueBookingBase):
    id: int
    venue_id: int
    customer_id: Optional[int] = None
    booking_reference: str
    booking_status: BookingStatus

    # Pricing details
    base_cost: Decimal
    facility_costs: Decimal = 0
    additional_costs: Decimal = 0
    discount_amount: Decimal = 0
    tax_amount: Decimal = 0
    total_cost: Decimal

    # Payment details
    deposit_amount: Optional[Decimal] = None
    deposit_paid_at: Optional[datetime] = None
    payment_due_date: Optional[datetime] = None
    payment_completed_at: Optional[datetime] = None

    # Status dates
    confirmed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancellation_reason: Optional[str] = None
    completed_at: Optional[datetime] = None

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Review Schemas
class VenueReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    review_text: Optional[str] = None

    # Detailed ratings (optional)
    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5)
    staff_rating: Optional[int] = Field(None, ge=1, le=5)
    facilities_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)
    location_rating: Optional[int] = Field(None, ge=1, le=5)

    is_public: bool = True


class VenueReviewCreate(VenueReviewBase):
    venue_id: int
    booking_id: Optional[int] = None


class VenueReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    review_text: Optional[str] = None

    cleanliness_rating: Optional[int] = Field(None, ge=1, le=5)
    staff_rating: Optional[int] = Field(None, ge=1, le=5)
    facilities_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)
    location_rating: Optional[int] = Field(None, ge=1, le=5)

    is_public: Optional[bool] = None
    venue_response: Optional[str] = None


class VenueReview(VenueReviewBase):
    id: int
    venue_id: int
    user_id: Optional[int] = None
    booking_id: Optional[int] = None

    is_verified: bool = False
    helpful_votes: int = 0

    venue_response: Optional[str] = None
    venue_responded_at: Optional[datetime] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Image Schemas
class VenueImageBase(BaseModel):
    url: str = Field(..., max_length=1000)
    filename: Optional[str] = Field(None, max_length=255)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    alt_text: Optional[str] = Field(None, max_length=200)
    image_type: Optional[str] = Field(None, max_length=50)
    is_primary: bool = False
    display_order: int = 0


class VenueImageCreate(VenueImageBase):
    venue_id: int


class VenueImageUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    alt_text: Optional[str] = Field(None, max_length=200)
    image_type: Optional[str] = Field(None, max_length=50)
    is_primary: Optional[bool] = None
    display_order: Optional[int] = None


class VenueImage(VenueImageBase):
    id: int
    venue_id: int
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    uploaded_at: datetime

    class Config:
        from_attributes = True


# Search and Filter Schemas
class VenueSearchParams(BaseModel):
    q: Optional[str] = None  # Search query
    city: Optional[str] = None
    region: Optional[str] = None
    venue_type: Optional[str] = None
    venue_status: Optional[VenueStatus] = VenueStatus.ACTIVE

    # Capacity filtering
    min_capacity: Optional[int] = Field(None, ge=1)
    max_capacity: Optional[int] = Field(None, ge=1)

    # Geographic filtering
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = Field(None, gt=0)

    # Pricing filtering
    max_price_per_hour: Optional[Decimal] = Field(None, ge=0)
    max_price_per_day: Optional[Decimal] = Field(None, ge=0)

    # Feature filtering
    has_parking: Optional[bool] = None
    has_catering: Optional[bool] = None
    has_av_equipment: Optional[bool] = None
    is_accessible: Optional[bool] = None

    # Availability filtering
    available_from: Optional[datetime] = None
    available_to: Optional[datetime] = None

    # Rating filtering
    min_rating: Optional[float] = Field(None, ge=0, le=5)

    # Pagination
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    # Sorting
    sort_by: Optional[str] = Field(
        default="name"
    )  # name, rating, price, distance, created_at
    sort_order: Optional[str] = Field(default="asc")  # asc, desc


class AvailabilitySearchParams(BaseModel):
    venue_id: int
    start_date: date
    end_date: date
    status_filter: Optional[AvailabilityStatus] = None


class BookingSearchParams(BaseModel):
    venue_id: Optional[int] = None
    customer_id: Optional[int] = None
    booking_status: Optional[BookingStatus] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


# Response Schemas
class VenueListResponse(BaseModel):
    venues: List[EnhancedVenue]
    total: int
    page: int
    size: int
    pages: int


class VenueAvailabilityResponse(BaseModel):
    availability_slots: List[VenueAvailability]
    total: int


class VenueBookingResponse(BaseModel):
    bookings: List[VenueBooking]
    total: int
    page: int
    size: int
    pages: int


class VenueReviewResponse(BaseModel):
    reviews: List[VenueReview]
    total: int
    average_rating: Optional[float] = None
    rating_distribution: Optional[Dict[int, int]] = None  # {1: count, 2: count, ...}


class FacilityResponse(BaseModel):
    facilities: List[Facility]
    total: int


# Statistics Schemas
class VenueStatistics(BaseModel):
    venue_id: int
    total_bookings: int
    total_revenue: Decimal
    average_rating: Optional[float]
    total_reviews: int
    occupancy_rate: float  # percentage
    most_popular_months: List[str]
    average_booking_value: Decimal
