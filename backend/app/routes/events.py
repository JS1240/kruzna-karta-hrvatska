import logging
from datetime import date
from decimal import Decimal
from math import asin, cos, radians, sin, sqrt
from typing import List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session, joinedload

logger = logging.getLogger(__name__)


def convert_decimal_coordinates(event):
    """Convert Decimal coordinates to float for proper JSON serialization."""
    if hasattr(event, 'latitude') and isinstance(event.latitude, Decimal):
        event.latitude = float(event.latitude)
    if hasattr(event, 'longitude') and isinstance(event.longitude, Decimal):
        event.longitude = float(event.longitude)
    
    # Also handle venue coordinates if present
    if hasattr(event, 'venue') and event.venue:
        venue = event.venue
        if hasattr(venue, 'latitude') and isinstance(venue.latitude, Decimal):
            venue.latitude = float(venue.latitude)
        if hasattr(venue, 'longitude') and isinstance(venue.longitude, Decimal):
            venue.longitude = float(venue.longitude)
    
    return event

from ..core.database import get_db, safe_db_operation, health_check_db, reset_database_connections
from ..core.events_service import EventsService
from ..core.geocoding_service import geocoding_service
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


# Safe wrapper functions for EventsService operations
def _safe_search_events(search_params: EventSearchParams, accept_language: Optional[str] = None):
    """Safe wrapper for EventsService.search_events with retry logic."""
    def _search_operation(db: Session):
        translation_service = get_translation_service()
        events_service = EventsService(db, translation_service)
        return events_service.search_events(search_params, accept_language)
    
    return safe_db_operation(_search_operation)


def _safe_get_featured_events(page: int = 1, size: int = 10):
    """Safe wrapper for getting featured events with retry logic."""
    def _featured_operation(db: Session):
        translation_service = get_translation_service()
        events_service = EventsService(db, translation_service)
        
        # Build search params for featured events
        search_params = EventSearchParams(
            page=page,
            size=size,
            is_featured=True
        )
        return events_service.search_events(search_params)
    
    return safe_db_operation(_featured_operation)


def _safe_get_events_paginated(search_params: EventSearchParams):
    """Safe wrapper for EventsService.get_events_paginated with retry logic."""
    def _paginated_operation(db: Session):
        translation_service = get_translation_service()
        events_service = EventsService(db, translation_service)
        
        events, total, pages = events_service.get_events_paginated(search_params)
        return {
            "events": events,
            "total": total,
            "pages": pages,
            "page": search_params.page,
            "size": search_params.size
        }
    
    return safe_db_operation(_paginated_operation)


@router.get("/", response_model=EventResponse)
def get_events(
    search_params: EventSearchParams = Depends(),
    accept_language: Optional[str] = Header(None),
):
    """Get events with comprehensive filtering, search, and geographic queries (safe database operations)."""
    try:
        logger.info(f"Getting events with params: page={search_params.page}, size={search_params.size}")
        
        # For simple queries, try optimized performance service first
        # Temporarily disabled to ensure coordinate conversion works
        if False and (search_params.use_cache and not search_params.q and 
            search_params.latitude is None and search_params.longitude is None and 
            not search_params.tags):
            
            def _performance_operation(db: Session):
                performance_service = get_performance_service(db)
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
            
            try:
                return safe_db_operation(_performance_operation)
            except Exception as e:
                logger.warning(f"Performance service fallback for events: {e}")
                # Fall through to regular events service but preserve exception context
                raise

        # Use safe events service for all other queries
        return _safe_search_events(search_params, accept_language)
        
    except Exception as e:
        logger.error(f"Error in get_events endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving events: {str(e)}"
        )


@router.get("/featured", response_model=EventResponse)
def get_featured_events(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
):
    """Get featured events with safe database operations."""
    try:
        logger.info(f"Getting featured events: page={page}, size={size}")
        return _safe_get_featured_events(page, size)
    except Exception as e:
        logger.error(f"Error in get_featured_events endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving featured events: {str(e)}"
        )


@router.get("/search", response_model=EventResponse)
def search_events(params: EventSearchParams = Depends()):
    """Advanced event search with all filters using safe database operations."""
    try:
        logger.info(f"Searching events with query: {params.q}")
        return _safe_search_events(params)
    except Exception as e:
        logger.error(f"Error in search_events endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Error searching events: {str(e)}"
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


@router.post("/geocode")
async def geocode_events(
    limit: int = Query(50, ge=1, le=200, description="Number of events to geocode"),
    db: Session = Depends(get_db),
):
    """Geocode events that don't have coordinates yet."""
    try:
        # Find events without coordinates
        events_without_coords = (
            db.query(Event)
            .filter(
                and_(
                    or_(Event.latitude.is_(None), Event.longitude.is_(None)),
                    Event.location.isnot(None),
                    Event.location != "",
                )
            )
            .limit(limit)
            .all()
        )

        if not events_without_coords:
            return {
                "message": "No events found that need geocoding",
                "geocoded_count": 0,
                "total_checked": 0,
            }

        # Prepare venues for batch geocoding
        venues_to_geocode = []
        for event in events_without_coords:
            venues_to_geocode.append((event.location, ""))

        # Batch geocode venues
        geocoding_results = await geocoding_service.batch_geocode_venues(
            venues_to_geocode
        )

        # Update events with coordinates
        geocoded_count = 0
        for event in events_without_coords:
            if event.location in geocoding_results:
                result = geocoding_results[event.location]
                event.latitude = result.latitude
                event.longitude = result.longitude
                geocoded_count += 1
                logger.info(
                    f"Geocoded event {event.id}: {event.location} → {result.latitude}, {result.longitude}"
                )

        # Commit changes
        db.commit()

        return {
            "message": f"Successfully geocoded {geocoded_count} events",
            "geocoded_count": geocoded_count,
            "total_checked": len(events_without_coords),
            "geocoding_results": [
                {
                    "location": location,
                    "latitude": result.latitude,
                    "longitude": result.longitude,
                    "confidence": result.confidence,
                    "accuracy": result.accuracy,
                }
                for location, result in geocoding_results.items()
            ],
        }

    except Exception as e:
        logger.error(f"Error geocoding events: {e}")
        raise HTTPException(status_code=500, detail=f"Error geocoding events: {str(e)}") from e


def _get_geocoding_status_data(db: Session):
    """Internal function to get geocoding status data."""
    # Count total events (only active ones)
    total_events = db.query(Event).filter(Event.event_status == "active").count()

    # Count events with coordinates
    events_with_coords = (
        db.query(Event)
        .filter(
            and_(
                Event.event_status == "active",
                Event.latitude.isnot(None),
                Event.longitude.isnot(None),
            )
        )
        .count()
    )

    # Count events without coordinates but with location
    events_need_geocoding = (
        db.query(Event)
        .filter(
            and_(
                Event.event_status == "active",
                or_(Event.latitude.is_(None), Event.longitude.is_(None)),
                Event.location.isnot(None),
                Event.location != "",
            )
        )
        .count()
    )

    # Count events without location
    events_without_location = (
        db.query(Event)
        .filter(
            and_(
                Event.event_status == "active",
                or_(Event.location.is_(None), Event.location == "")
            )
        )
        .count()
    )

    geocoding_percentage = round(
        (events_with_coords / total_events * 100) if total_events > 0 else 0, 1
    )

    return {
        "total_events": total_events,
        "events_with_coordinates": events_with_coords,
        "events_need_geocoding": events_need_geocoding,
        "events_without_location": events_without_location,
        "geocoding_percentage": geocoding_percentage,
    }


@router.get("/geocoding-status/")
def get_geocoding_status():
    """Get the current geocoding status for events."""
    try:
        # Use safe database operation with retry logic
        result = safe_db_operation(_get_geocoding_status_data)
        
        logger.info(f"Geocoding status: {result['events_with_coordinates']}/{result['total_events']} events geocoded ({result['geocoding_percentage']}%)")
        
        return result

    except Exception as e:
        logger.error(f"Error getting geocoding status: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error getting geocoding status: {str(e)}"
        )


@router.get("/db-health/")
def get_database_health():
    """Get database health status and connection info."""
    try:
        health_result = health_check_db()
        logger.info(f"Database health check: {health_result['status']}")
        return health_result
    except Exception as e:
        logger.error(f"Error checking database health: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }


@router.post("/db-reset/")
def reset_database_pool():
    """Reset database connection pool (admin endpoint)."""
    try:
        reset_success = reset_database_connections()
        if reset_success:
            return {"status": "success", "message": "Database connections reset"}
        else:
            return {"status": "failed", "message": "Failed to reset connections"}
    except Exception as e:
        logger.error(f"Error resetting database: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Error resetting database: {str(e)}"
        )


@router.get("/debug-coordinates/")
def debug_coordinates(db: Session = Depends(get_db)):
    """Debug endpoint to check coordinate values."""
    try:
        event = db.query(Event).filter(Event.id == 7).first()
        if not event:
            return {"error": "Event not found"}
        
        result = {
            "event_id": event.id,
            "title": event.title,
            "latitude_raw": event.latitude,
            "longitude_raw": event.longitude,
            "latitude_type": type(event.latitude).__name__,
            "longitude_type": type(event.longitude).__name__,
            "latitude_str": str(event.latitude) if event.latitude else None,
            "longitude_str": str(event.longitude) if event.longitude else None,
        }
        
        if event.latitude:
            result["latitude_float"] = float(event.latitude)
        if event.longitude:
            result["longitude_float"] = float(event.longitude)
            
        return result
        
    except Exception as e:
        logger.error(f"Error in debug_coordinates: {e}", exc_info=True)
        return {"error": str(e)}


@router.get("/data-integrity/")
def check_data_integrity(db: Session = Depends(get_db)):
    """Check critical data integrity issues that could cause UI problems."""
    try:
        issues = []
        warnings = []
        
        # Check for events with missing coordinates
        events_without_coords = db.query(Event).filter(
            or_(Event.latitude.is_(None), Event.longitude.is_(None))
        ).count()
        
        if events_without_coords > 0:
            issues.append(f"{events_without_coords} events missing coordinates - will not appear on map")
        
        # Check for featured events with issues
        featured_events_with_coords = db.query(Event).filter(
            and_(
                Event.is_featured == True,
                Event.latitude.isnot(None),
                Event.longitude.isnot(None)
            )
        ).count()
        
        total_featured = db.query(Event).filter(Event.is_featured == True).count()
        
        if featured_events_with_coords < total_featured:
            issues.append(f"{total_featured - featured_events_with_coords} featured events missing coordinates")
        
        # Check API response serialization by testing actual endpoints
        try:
            events_response = _safe_search_events(EventSearchParams(page=1, size=1))
            if events_response and hasattr(events_response, 'events') and len(events_response.events) > 0:
                test_event = events_response.events[0]
                if hasattr(test_event, 'latitude') and test_event.latitude is None:
                    issues.append("API serialization issue: coordinates returning null")
        except Exception as api_error:
            issues.append(f"API test failed: {str(api_error)}")
        
        # Check database connection health
        try:
            db.execute(text("SELECT 1")).scalar()
        except Exception as db_error:
            issues.append(f"Database connection issue: {str(db_error)}")
        
        return {
            "status": "healthy" if len(issues) == 0 else "issues_found",
            "total_events": db.query(Event).count(),
            "featured_events": total_featured,
            "events_with_coordinates": db.query(Event).filter(
                and_(Event.latitude.isnot(None), Event.longitude.isnot(None))
            ).count(),
            "issues": issues,
            "warnings": warnings,
            "checks_performed": [
                "coordinate_completeness",
                "featured_event_coordinates", 
                "api_serialization",
                "database_connectivity"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error in data_integrity check: {e}", exc_info=True)
        return {
            "status": "error",
            "error": str(e)
        }
