from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, text, and_, or_
from typing import List, Optional
from datetime import date
from math import radians, cos, sin, asin, sqrt
import logging

logger = logging.getLogger(__name__)

from ..core.database import get_db
from ..core.translation import TranslationService, get_translation_service, DEFAULT_LANGUAGE
from ..core.performance import get_performance_service, PerformanceService
from ..models.event import Event
from ..models.category import EventCategory
from ..models.venue import Venue
from ..models import schemas
from ..models.schemas import (
    EventCreate, 
    EventUpdate, 
    EventResponse,
    EventSearchParams
)

router = APIRouter(prefix="/events", tags=["events"])



def get_language_from_header(accept_language: Optional[str] = Header(None)) -> str:
    """Extract language preference from Accept-Language header."""
    if accept_language:
        # Parse Accept-Language header (e.g., "hr,en;q=0.9,de;q=0.8")
        languages = []
        for lang_part in accept_language.split(','):
            lang = lang_part.split(';')[0].strip()
            if len(lang) == 2:  # Only accept 2-letter codes
                languages.append(lang)
        
        # Return first supported language
        supported = ['hr', 'en', 'de', 'it', 'sl']
        for lang in languages:
            if lang in supported:
                return lang
    
    return DEFAULT_LANGUAGE


@router.get("/", response_model=EventResponse)
def get_events(
    q: Optional[str] = Query(None, description="Search query for full-text search"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    venue_id: Optional[int] = Query(None, description="Filter by venue ID"),
    city: Optional[str] = Query(None, description="Filter by city"),
    date_from: Optional[date] = Query(None, description="Filter events from this date"),
    date_to: Optional[date] = Query(None, description="Filter events until this date"),
    is_featured: Optional[bool] = Query(None, description="Filter featured events"),
    event_status: Optional[str] = Query("active", description="Filter by event status"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    latitude: Optional[float] = Query(None, description="Latitude for geographic search"),
    longitude: Optional[float] = Query(None, description="Longitude for geographic search"),
    radius_km: Optional[float] = Query(None, description="Search radius in kilometers"),
    language: Optional[str] = Query(None, description="Language code for translations"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    use_cache: bool = Query(True, description="Use cached results for better performance"),
    accept_language: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    performance_service: PerformanceService = Depends(get_performance_service)
):
    """Get events with comprehensive filtering, search, and geographic queries (optimized with caching)."""
    
    # Determine language for translations
    if not language:
        language = get_language_from_header(accept_language)
    
    # Use optimized service for simple queries (no search, no geographic filtering)
    if use_cache and not q and latitude is None and longitude is None and not tags:
        try:
            result = performance_service.get_events_optimized(
                page=page,
                size=size,
                category_id=category_id,
                venue_id=venue_id,
                city=city,
                date_from=date_from,
                date_to=date_to,
                is_featured=is_featured,
                language=language
            )
            
            return EventResponse(
                events=[schemas.Event(**event_data) for event_data in result["events"]],
                total=result["total"],
                page=result["page"],
                size=result["size"],
                pages=result["pages"]
            )
        except Exception as e:
            # Fallback to non-cached version
            logger.warning(f"Cache fallback for events: {e}")
    
    # Original non-cached implementation for complex queries
    query = db.query(Event).options(
        joinedload(Event.category),
        joinedload(Event.venue)
    )
    
    # Apply filters
    if q:
        query = query.filter(Event.search_vector.match(q))
    
    if category_id:
        query = query.filter(Event.category_id == category_id)
    
    if venue_id:
        query = query.filter(Event.venue_id == venue_id)
    
    if city:
        query = query.filter(Event.location.ilike(f"%{city}%"))
    
    if date_from:
        query = query.filter(Event.date >= date_from)
    
    if date_to:
        query = query.filter(Event.date <= date_to)
    
    if is_featured is not None:
        query = query.filter(Event.is_featured == is_featured)
    
    if event_status:
        query = query.filter(Event.event_status == event_status)
    
    if tags:
        for tag in tags:
            query = query.filter(Event.tags.any(tag))
    
    # Geographic filtering
    if latitude is not None and longitude is not None and radius_km is not None:
        query = query.filter(
            func.earth_distance(
                func.ll_to_earth(Event.latitude, Event.longitude),
                func.ll_to_earth(latitude, longitude)
            ) <= radius_km * 1000
        )
    
    # Get total count and apply pagination
    total = query.count()
    skip = (page - 1) * size
    pages = (total + size - 1) // size if total > 0 else 0
    
    events = query.order_by(
        Event.is_featured.desc(),
        Event.date.asc(), 
        Event.time.asc()
    ).offset(skip).limit(size).all()
    
    return EventResponse(
        events=events,
        total=total,
        page=page,
        size=len(events),
        pages=pages
    )


@router.get("/featured", response_model=EventResponse)
def get_featured_events(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get featured events."""
    query = db.query(Event).options(
        joinedload(Event.category),
        joinedload(Event.venue)
    ).filter(Event.is_featured == True, Event.event_status == 'active')
    
    total = query.count()
    skip = (page - 1) * size
    pages = (total + size - 1) // size if total > 0 else 0
    
    events = query.order_by(Event.date.asc()).offset(skip).limit(size).all()
    
    return EventResponse(
        events=events,
        total=total,
        page=page,
        size=len(events),
        pages=pages
    )


@router.get("/search", response_model=EventResponse)
def search_events(
    params: EventSearchParams = Depends(),
    db: Session = Depends(get_db)
):
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
        db=db
    )


@router.get("/nearby", response_model=EventResponse)
def get_nearby_events(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    radius_km: float = Query(10, description="Search radius in kilometers"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get events near a specific location."""
    return get_events(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        page=page,
        size=size,
        db=db
    )


@router.get("/{event_id}", response_model=schemas.Event)
def get_event(
    event_id: int, 
    language: Optional[str] = Query("hr", description="Language code for translations"),
    use_cache: bool = Query(True, description="Use cached results for better performance"),
    accept_language: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    performance_service = Depends(get_performance_service)
):
    """Get a specific event by ID with related data (optimized with caching)."""
    
    # Determine language
    if not language:
        language = get_language_from_header(accept_language)
    
    # Try cached version first
    if use_cache:
        try:
            cached_event = performance_service.get_event_detail_optimized(event_id, language)
            if cached_event:
                return schemas.Event(**cached_event)
        except Exception as e:
            logger.warning(f"Cache fallback for event {event_id}: {e}")
    
    # Fallback to direct database query
    event = db.query(Event).options(
        joinedload(Event.category),
        joinedload(Event.venue)
    ).filter(Event.id == event_id).first()
    
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Increment view count
    event.view_count = (event.view_count or 0) + 1
    db.commit()
    
    return event


@router.get("/slug/{slug}", response_model=schemas.Event)
def get_event_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a specific event by slug."""
    event = db.query(Event).options(
        joinedload(Event.category),
        joinedload(Event.venue)
    ).filter(Event.slug == slug).first()
    
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
    db_event = db.query(Event).options(
        joinedload(Event.category),
        joinedload(Event.venue)
    ).filter(Event.id == event_id).first()
    
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
        "city": db_event.location.split(",")[0].strip() if db_event.location else None
    }
    
    # Enrich with Croatian context
    croatian_service = get_croatian_events_service()
    enriched_event = croatian_service.enrich_event_with_croatian_context(event_data)
    
    return {
        "event": db_event,
        "croatian_context": enriched_event
    }


@router.get("/croatian-recommendations")
def get_croatian_event_recommendations(
    event_type: str = Query(..., description="Type of event (e.g., 'cultural festival', 'outdoor concert')"),
    city: Optional[str] = Query(None, description="City in Croatia"),
    month: Optional[int] = Query(None, description="Month for recommendations (1-12)"),
    db: Session = Depends(get_db)
):
    """Get Croatian-specific event recommendations and timing suggestions."""
    from ..core.croatian import get_croatian_events_service, get_croatian_holiday_service
    from datetime import datetime
    
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
    timing_suggestions = croatian_service.suggest_croatian_event_timing(event_type, region)
    
    # Get seasonal recommendations
    seasonal_recommendations = []
    if region:
        seasonal_recommendations = holiday_service.get_seasonal_events_recommendation(region, month)
    
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
                "is_work_free": h.is_work_free
            } for h in upcoming_holidays
        ],
        "cultural_categories": cultural_categories
    }