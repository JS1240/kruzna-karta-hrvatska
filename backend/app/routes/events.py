import logging
from datetime import date
from math import asin, cos, radians, sin, sqrt
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)

from ..core.database import get_db
from ..core.events_service import EventsService
from ..core.performance import PerformanceService, get_performance_service
from ..core.translation import (
    DEFAULT_LANGUAGE,
    TranslationService,
    get_translation_service,
)
from ..models import schemas
from ..models.category import EventCategory
from ..models.event import Event
from ..models.schemas import EventCreate, EventResponse, EventSearchParams, EventUpdate
from ..models.venue import Venue

router = APIRouter(prefix="/events", tags=["events"])


def get_language_from_header(accept_language: Optional[str] = Header(None)) -> str:
    """Extract language preference from Accept-Language header."""
    if accept_language:
        # Parse Accept-Language header (e.g., "hr,en;q=0.9,de;q=0.8")
        languages = []
        for lang_part in accept_language.split(","):
            lang = lang_part.split(";")[0].strip()
            if len(lang) == 2:  # Only accept 2-letter codes
                languages.append(lang)

        # Return first supported language
        supported = ["hr", "en", "de", "it", "sl"]
        for lang in languages:
            if lang in supported:
                return lang

    return DEFAULT_LANGUAGE


@router.get("/", response_model=EventResponse)
def get_events(
    search_params: EventSearchParams = Depends(),
    accept_language: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    performance_service: PerformanceService = Depends(get_performance_service),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Get events with comprehensive filtering, search, and geographic queries (optimized with caching)."""
    
    # Create events service
    events_service = EventsService(db, translation_service)
    
    # Use optimized performance service for simple queries (no search, no geographic filtering)
    if (search_params.use_cache and not search_params.q and 
        search_params.latitude is None and search_params.longitude is None and 
        not search_params.tags):
        try:
            result = performance_service.get_events_optimized(
                page=search_params.page,
                size=search_params.size,
                category_id=search_params.category_id,
                venue_id=search_params.venue_id,
                city=search_params.city,
                date_from=search_params.date_from,
                date_to=search_params.date_to,
                is_featured=search_params.is_featured,
                language=search_params.language,
            )

            return EventResponse(
                events=[schemas.Event(**event_data) for event_data in result["events"]],
                total=result["total"],
                page=result["page"],
                size=result["size"],
                pages=result["pages"],
            )
        except Exception as e:
            # Fallback to non-cached version
            logger.warning(f"Cache fallback for events: {e}")

    # Use events service for all other queries
    return events_service.search_events(search_params, accept_language)


@router.get("/featured", response_model=EventResponse)
def get_featured_events(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get featured events."""
    query = (
        db.query(Event)
        .options(joinedload(Event.category), joinedload(Event.venue))
        .filter(Event.is_featured == True, Event.event_status == "active")
    )

    total = query.count()
    skip = (page - 1) * size
    pages = (total + size - 1) // size if total > 0 else 0

    events = query.order_by(Event.date.asc()).offset(skip).limit(size).all()

    return EventResponse(
        events=events, total=total, page=page, size=len(events), pages=pages
    )


@router.get("/search", response_model=EventResponse)
def search_events(params: EventSearchParams = Depends(), db: Session = Depends(get_db)):
    """Advanced event search with all filters."""
    return get_events(
        q=params.q,
        category_id=params.category_id,
        venue_id=params.venue_id,
        city=params.city,
        date_from=params.date_from,
        date_to=params.date_to,
        is_featured=params.is_featured,
        event_status=params.event_status,
        tags=params.tags,
        latitude=params.latitude,
        longitude=params.longitude,
        radius_km=params.radius_km,
        page=params.page,
        size=params.size,
        db=db,
    )


@router.get("/nearby", response_model=EventResponse)
def get_nearby_events(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    radius_km: float = Query(10, description="Search radius in kilometers"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get events near a specific location."""
    return get_events(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        page=page,
        size=size,
        db=db,
    )


@router.get("/{event_id}", response_model=schemas.Event)
def get_event(
    event_id: int,
    language: Optional[str] = Query("hr", description="Language code for translations"),
    use_cache: bool = Query(
        True, description="Use cached results for better performance"
    ),
    accept_language: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    performance_service=Depends(get_performance_service),
):
    """Get a specific event by ID with related data (optimized with caching)."""

    # Determine language
    if not language:
        language = get_language_from_header(accept_language)

    # Try cached version first
    if use_cache:
        try:
            cached_event = performance_service.get_event_detail_optimized(
                event_id, language
            )
            if cached_event:
                return schemas.Event(**cached_event)
        except Exception as e:
            logger.warning(f"Cache fallback for event {event_id}: {e}")

    # Fallback to direct database query
    event = (
        db.query(Event)
        .options(joinedload(Event.category), joinedload(Event.venue))
        .filter(Event.id == event_id)
        .first()
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Increment view count
    event.view_count = (event.view_count or 0) + 1
    db.commit()

    return event


@router.get("/slug/{slug}", response_model=schemas.Event)
def get_event_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a specific event by slug."""
    event = (
        db.query(Event)
        .options(joinedload(Event.category), joinedload(Event.venue))
        .filter(Event.slug == slug)
        .first()
    )

    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Increment view count
    event.view_count = (event.view_count or 0) + 1
    db.commit()

    return event


@router.post("/", response_model=schemas.Event)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event."""
    db_event = Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.put("/{event_id}", response_model=schemas.Event)
def update_event(event_id: int, event: EventUpdate, db: Session = Depends(get_db)):
    """Update an existing event."""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Update only provided fields
    update_data = event.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)
    return db_event


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)):
    """Delete an event."""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    db.delete(db_event)
    db.commit()
    return {"message": "Event deleted successfully"}


@router.get("/{event_id}/croatian-context")
def get_event_with_croatian_context(event_id: int, db: Session = Depends(get_db)):
    """Get event enriched with Croatian cultural context."""
    from ..core.croatian import get_croatian_events_service

    # Get the event
    db_event = (
        db.query(Event)
        .options(joinedload(Event.category), joinedload(Event.venue))
        .filter(Event.id == event_id)
        .first()
    )

    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Convert to dict for enrichment
    event_data = {
        "id": db_event.id,
        "title": db_event.title,
        "description": db_event.description,
        "date": db_event.date.isoformat() if db_event.date else None,
        "time": str(db_event.time) if db_event.time else None,
        "location": db_event.location,
        "price": float(db_event.price) if db_event.price else None,
        "currency": "EUR",  # Croatian default currency
        "category": db_event.category.name if db_event.category else None,
        "venue": db_event.venue.name if db_event.venue else None,
        "city": db_event.location.split(",")[0].strip() if db_event.location else None,
    }

    # Enrich with Croatian context
    croatian_service = get_croatian_events_service()
    enriched_event = croatian_service.enrich_event_with_croatian_context(event_data)

    return {"event": db_event, "croatian_context": enriched_event}


@router.get("/croatian-recommendations")
def get_croatian_event_recommendations(
    event_type: str = Query(
        ..., description="Type of event (e.g., 'cultural festival', 'outdoor concert')"
    ),
    city: Optional[str] = Query(None, description="City in Croatia"),
    month: Optional[int] = Query(None, description="Month for recommendations (1-12)"),
    db: Session = Depends(get_db),
):
    """Get Croatian-specific event recommendations and timing suggestions."""
    from datetime import datetime

    from ..core.croatian import (
        get_croatian_events_service,
        get_croatian_holiday_service,
    )

    croatian_service = get_croatian_events_service()
    holiday_service = get_croatian_holiday_service()

    # Determine region if city provided
    region = None
    if city:
        region = holiday_service.get_region_by_city(city)

    # Use current month if not specified
    if not month:
        month = datetime.now().month

    # Get timing suggestions
    timing_suggestions = croatian_service.suggest_croatian_event_timing(
        event_type, region
    )

    # Get seasonal recommendations
    seasonal_recommendations = []
    if region:
        seasonal_recommendations = holiday_service.get_seasonal_events_recommendation(
            region, month
        )

    # Get upcoming Croatian holidays
    upcoming_holidays = holiday_service.get_upcoming_holidays(90)  # Next 3 months

    # Get cultural categories
    cultural_categories = croatian_service.get_croatian_cultural_categories()

    return {
        "event_type": event_type,
        "city": city,
        "region": region.value if region else None,
        "month": month,
        "timing_suggestions": timing_suggestions,
        "seasonal_recommendations": seasonal_recommendations,
        "upcoming_holidays": [
            {
                "name": h.name,
                "name_hr": h.name_hr,
                "date": h.date.isoformat(),
                "type": h.holiday_type.value,
                "is_work_free": h.is_work_free,
            }
            for h in upcoming_holidays
        ],
        "cultural_categories": cultural_categories,
    }
