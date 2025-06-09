from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


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
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    capacity: Optional[int] = None
    venue_type: Optional[str] = Field(None, max_length=50)
    website: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=255)


class VenueCreate(VenueBase):
    pass


class VenueUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
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
    name: str = Field(..., max_length=500)
    time: str = Field(..., max_length=50)
    date: date
    price: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    link: Optional[str] = Field(None, max_length=1000)
    image: Optional[str] = Field(None, max_length=1000)
    location: str = Field(..., max_length=500)
    category_id: Optional[int] = None
    venue_id: Optional[int] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
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


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    time: Optional[str] = Field(None, max_length=50)
    date: Optional[date] = None
    price: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    link: Optional[str] = Field(None, max_length=1000)
    image: Optional[str] = Field(None, max_length=1000)
    location: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    venue_id: Optional[int] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
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
    q: Optional[str] = None  # Search query
    category_id: Optional[int] = None
    venue_id: Optional[int] = None
    city: Optional[str] = None
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    is_featured: Optional[bool] = None
    event_status: Optional[str] = "active"
    tags: Optional[List[str]] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None  # Search radius in kilometers
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class VenueSearchParams(BaseModel):
    q: Optional[str] = None
    city: Optional[str] = None
    venue_type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
