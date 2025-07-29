from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# Event Category Schemas
class EventCategoryBase(BaseModel):
    name: str = Field(..., max_length=100)
    slug: str = Field(..., max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(default="#3B82F6", max_length=7)
    icon: Optional[str] = Field(None, max_length=50)


class EventCategoryCreate(EventCategoryBase):
    pass


class EventCategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    slug: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = Field(None, max_length=7)
    icon: Optional[str] = Field(None, max_length=50)


class EventCategory(EventCategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


# Venue Schemas
class VenueBase(BaseModel):
    name: str = Field(..., max_length=255)
    address: Optional[str] = None
    city: str = Field(..., max_length=100)
    country: Optional[str] = Field(default="Croatia", max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: Optional[int] = None
    venue_type: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)

    @field_validator('latitude', 'longitude', mode='before')
    @classmethod
    def convert_decimal_to_float(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v


class VenueCreate(VenueBase):
    pass


class VenueUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: Optional[int] = None
    venue_type: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)


class Venue(VenueBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Event Schemas
class EventBase(BaseModel):
    title: str = Field(..., max_length=500)
    time: str = Field(..., max_length=50)
    date: date
    price: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    link: Optional[str] = Field(None, max_length=1000)
    image: Optional[str] = Field(None, max_length=1000)
    location: str = Field(..., max_length=500)
    category_id: Optional[int] = None
    venue_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: str = Field(default="manual", max_length=50)
    external_id: Optional[str] = Field(None, max_length=255)
    event_status: Optional[str] = Field(default="active", max_length=20)
    is_featured: Optional[bool] = Field(default=False)
    is_recurring: Optional[bool] = Field(default=False)
    organizer: Optional[str] = Field(None, max_length=255)
    age_restriction: Optional[str] = Field(None, max_length=50)
    ticket_types: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    slug: Optional[str] = Field(None, max_length=600)
    end_date: Optional[date] = None
    end_time: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(default="Europe/Zagreb", max_length=50)

    @field_validator('latitude', 'longitude', mode='before')
    @classmethod
    def convert_decimal_to_float(cls, v):
        if isinstance(v, Decimal):
            return float(v)
        return v


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    time: Optional[str] = Field(None, max_length=50)
    date: Optional[date] = None
    price: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    link: Optional[str] = Field(None, max_length=1000)
    image: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    venue_id: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    source: Optional[str] = Field(None, max_length=50)
    external_id: Optional[str] = Field(None, max_length=255)
    event_status: Optional[str] = Field(None, max_length=20)
    is_featured: Optional[bool] = None
    is_recurring: Optional[bool] = None
    organizer: Optional[str] = Field(None, max_length=255)
    age_restriction: Optional[str] = Field(None, max_length=50)
    ticket_types: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    slug: Optional[str] = Field(None, max_length=600)
    end_date: Optional[date] = None
    end_time: Optional[str] = Field(None, max_length=50)
    timezone: Optional[str] = Field(None, max_length=50)


class Event(EventBase):
    id: int
    view_count: int
    last_scraped_at: Optional[datetime] = None
    scrape_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Nested objects
    category: Optional[EventCategory] = None
    venue: Optional[Venue] = None

    class Config:
        from_attributes = True


# Response Schemas
class EventResponse(BaseModel):
    events: List[Event]
    total: int
    page: int
    size: int
    pages: int


class CategoryResponse(BaseModel):
    categories: List[EventCategory]
    total: int


class VenueResponse(BaseModel):
    venues: List[Venue]
    total: int
    page: int
    size: int
    pages: int


# Search and Filter Schemas
class EventSearchParams(BaseModel):
    q: Optional[str] = Field(None, description="Search query for full-text search")
    category_id: Optional[int] = Field(None, description="Filter by category ID")
    venue_id: Optional[int] = Field(None, description="Filter by venue ID")
    city: Optional[str] = Field(None, description="Filter by city")
    date_from: Optional[date] = Field(None, description="Filter events from this date")
    date_to: Optional[date] = Field(None, description="Filter events until this date")
    is_featured: Optional[bool] = Field(None, description="Filter featured events")
    event_status: Optional[str] = Field("active", description="Filter by event status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    latitude: Optional[float] = Field(None, description="Latitude for geographic search")
    longitude: Optional[float] = Field(None, description="Longitude for geographic search")
    radius_km: Optional[float] = Field(None, description="Search radius in kilometers")
    language: Optional[str] = Field(None, description="Language code for translations")
    page: int = Field(default=1, ge=1, description="Page number")
    size: int = Field(default=20, ge=1, le=100, description="Page size")
    use_cache: bool = Field(default=True, description="Use cached results for better performance")


class VenueSearchParams(BaseModel):
    q: Optional[str] = None
    city: Optional[str] = None
    venue_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
