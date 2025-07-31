import logging
from decimal import Decimal
from typing import Any, Dict, Optional, Union

from fastapi import APIRouter, Depends, Header, Query
from sqlalchemy import and_, or_, text
from sqlalchemy.orm import Session, joinedload

from app.core.error_handlers import (
    EventNotFoundError,
    DatabaseOperationError,
    ExternalServiceError
)

logger = logging.getLogger(__name__)


def convert_decimal_coordinates(event: Any) -> Any:
    """Convert Decimal coordinates to float for proper JSON serialization.
    
    Args:
        event: Event object with potential Decimal coordinate attributes
        
    Returns:
        Event object with float coordinates for JSON serialization
    """
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

from app.core.database import get_db, safe_db_operation, health_check_db, reset_database_connections
from app.core.events_service import EventsService
from app.core.geocoding_service import geocoding_service
# Performance service removed for MVP simplification
from app.core.translation import (
    DEFAULT_LANGUAGE,
    get_translation_service,
)
from app.models import schemas
from app.models.event import Event
from app.models.schemas import EventCreate, EventResponse, EventSearchParams, EventUpdate

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
    """Get events with comprehensive filtering, search, and geographic queries.
    
    Primary API endpoint for retrieving events from the Croatian events platform.
    Supports full-text search, category/venue filtering, date ranges, geographic
    search, and pagination. Uses safe database operations with automatic retry
    and transaction handling.
    
    Args:
        search_params: Search and filter parameters including:
            - q: Full-text search query (searches title, description, location)
            - category_id: Filter by specific event category
            - venue_id: Filter by specific venue
            - city: Filter by city name
            - date_from: Start date for date range filtering
            - date_to: End date for date range filtering  
            - is_featured: Filter for featured events only
            - event_status: Filter by status (default: "active")
            - tags: Filter by event tags
            - latitude/longitude/radius_km: Geographic search parameters
            - language: Language code for translations
            - page: Page number for pagination (default: 1)
            - size: Items per page (default: 20, max: 100)
        accept_language: HTTP Accept-Language header for automatic language detection
        
    Returns:
        EventResponse: Paginated response containing:
            - events: List of matching Event objects with full details
            - total: Total number of matching events
            - page: Current page number
            - size: Number of items returned
            - pages: Total number of pages available
            
    Raises:
        DatabaseOperationError: If database operations fail
        ExternalServiceError: If external services are unavailable
        
    Note:
        Uses centralized exception handling for consistent error responses
    """
    logger.info(f"Getting events with params: page={search_params.page}, size={search_params.size}")
    
    # Use safe events service (performance optimization removed for MVP)
    # Let centralized exception handlers manage any errors that bubble up
    return _safe_search_events(search_params, accept_language)


@router.get("/featured", response_model=EventResponse)
def get_featured_events(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
):
    """Get featured events with safe database operations.
    
    Uses centralized exception handling for consistent error responses.
    """
    logger.info(f"Getting featured events: page={page}, size={size}")
    return _safe_get_featured_events(page, size)


@router.get("/search", response_model=EventResponse)
def search_events(params: EventSearchParams = Depends()) -> EventResponse:
    """Advanced event search with comprehensive filtering capabilities.
    
    Dedicated search endpoint providing the same functionality as the main events
    endpoint but with explicit search semantics. Supports full-text search across
    event title, description, and location fields, combined with category, venue,
    date, and geographic filtering.
    
    Args:
        params: Complete search parameters including all EventSearchParams fields:
            - q: Search query string for full-text search
            - category_id: Filter by event category ID
            - venue_id: Filter by venue ID
            - city: Filter by city name
            - date_from/date_to: Date range filtering
            - is_featured: Featured events filter
            - latitude/longitude/radius_km: Geographic proximity search
            - tags: Tag-based filtering
            - page/size: Pagination controls
            
    Returns:
        EventResponse: Search results with pagination metadata:
            - events: List of matching events sorted by relevance/date
            - total: Total number of search results
            - page: Current page number
            - size: Results per page
            - pages: Total pages available
            
    Raises:
        DatabaseOperationError: If database operations fail
        ExternalServiceError: If external services are unavailable
        
    Note:
        Uses centralized exception handling for consistent error responses.
    """
    logger.info(f"Searching events with query: {params.q}")
    return _safe_search_events(params)


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
    # Performance service removed for MVP
):
    """Get a specific event by ID with complete details and related data.
    
    Retrieves a single event with full information including category and venue
    details. Supports localization and caching for optimal performance. 
    Automatically increments the event's view count for analytics.
    
    Args:
        event_id: Unique identifier of the event to retrieve
        language: Language code for localized content (default: "hr" Croatian)
        use_cache: Whether to use cached results for better performance (default: True)
        accept_language: HTTP Accept-Language header for automatic language detection
        db: Database session dependency (automatically injected)
        
    Returns:
        Event: Complete event object including:
            - Basic event information (title, description, date, time)
            - Category details (name, slug, description)
            - Venue information (name, address, coordinates)
            - Pricing and booking information
            - Localized content based on language parameter
            - Updated view count
            
    Raises:
        EventNotFoundError: If event with given ID is not found
    """

    # Determine language
    if not language:
        language = get_language_from_header(accept_language)

    # Direct database query (performance optimization removed for MVP)
    event = (
        db.query(Event)
        .options(joinedload(Event.category), joinedload(Event.venue))
        .filter(Event.id == event_id)
        .first()
    )

    if not event:
        raise EventNotFoundError(event_id)

    # Increment view count
    event.view_count = (event.view_count or 0) + 1
    db.commit()

    return event


@router.get("/slug/{slug}", response_model=schemas.Event)
def get_event_by_slug(slug: str, db: Session = Depends(get_db)) -> schemas.Event:
    """Get a specific event by slug."""
    event = (
        db.query(Event)
        .options(joinedload(Event.category), joinedload(Event.venue))
        .filter(Event.slug == slug)
        .first()
    )

    if not event:
        raise EventNotFoundError(event_id)

    # Increment view count
    event.view_count = (event.view_count or 0) + 1
    db.commit()

    return event


@router.post("/", response_model=schemas.Event)
def create_event(event: EventCreate, db: Session = Depends(get_db)) -> schemas.Event:
    """Create a new event."""
    db_event = Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.put("/{event_id}", response_model=schemas.Event)
def update_event(event_id: int, event: EventUpdate, db: Session = Depends(get_db)) -> schemas.Event:
    """Update an existing event."""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise EventNotFoundError(event_id)

    # Update only provided fields
    update_data = event.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)

    db.commit()
    db.refresh(db_event)
    return db_event


@router.delete("/{event_id}")
def delete_event(event_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Delete an event."""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if not db_event:
        raise EventNotFoundError(event_id)

    db.delete(db_event)
    db.commit()
    return {"message": "Event deleted successfully"}






@router.post("/geocode")
async def geocode_events(
    limit: int = Query(50, ge=1, le=200, description="Number of events to geocode"),
    db: Session = Depends(get_db),
):
    """Batch geocode events that are missing latitude/longitude coordinates.
    
    Administrative endpoint for improving data quality by adding geographic
    coordinates to events that have location names but missing lat/lng data.
    Uses external geocoding service to convert location strings to coordinates
    for map display and proximity search functionality.
    
    Args:
        limit: Maximum number of events to process in this batch (1-200, default: 50)
            Used to prevent timeouts and manage API rate limits
        db: Database session dependency (automatically injected)
        
    Returns:
        Dict containing geocoding operation results:
            - message: Human-readable status message
            - geocoded_count: Number of events successfully geocoded
            - total_checked: Number of events examined for geocoding
            - geocoding_results: List of geocoding results with:
                - location: Original location string
                - latitude: Resolved latitude coordinate
                - longitude: Resolved longitude coordinate
                - confidence: Geocoding confidence score
                - accuracy: Geographic accuracy level
                
    Raises:
        ExternalServiceError: If geocoding service fails
        DatabaseOperationError: If database operation fails
    """
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
        # Check if this is a geocoding service error
        if "geocoding" in str(e).lower() or "geocoding_service" in str(e).lower():
            raise ExternalServiceError("geocoding", "batch geocode venues", e)
        else:
            # Re-raise as database error or let centralized handler manage it
            raise


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
def get_geocoding_status() -> Dict[str, Union[int, float]]:
    """Get the current geocoding status for events.
    
    Uses centralized exception handling for consistent error responses.
    """
    # Use safe database operation with retry logic
    result = safe_db_operation(_get_geocoding_status_data)
    
    logger.info(f"Geocoding status: {result['events_with_coordinates']}/{result['total_events']} events geocoded ({result['geocoding_percentage']}%)")
    
    return result


@router.get("/db-health/")
def get_database_health() -> Dict[str, Any]:
    """Get comprehensive database health status and connection information.
    
    Administrative endpoint providing detailed database health metrics for
    monitoring and debugging purposes. Performs connectivity tests, connection
    pool analysis, and data integrity checks to ensure the database system
    is operating correctly.
    
    Returns:
        Dict containing health status information:
            - status: Overall health status ("healthy" or "unhealthy")
            - database_connected: Boolean indicating successful database connection
            - pool_status: Connection pool metrics (size, checked in/out, overflow)
            - connectivity: Connection test result ("ok" or error details)
            - event_table: Specific test result for events table accessibility
            - error: Error message if health check fails (only present on failure)
            - reset_attempted: Boolean indicating if connection reset was attempted
            
    Note:
        This endpoint does not require authentication but should be restricted
        to monitoring systems and administrators in production environments.
    """
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
def reset_database_pool() -> Dict[str, str]:
    """Reset database connection pool (admin endpoint)."""
    try:
        reset_success = reset_database_connections()
        if reset_success:
            return {"status": "success", "message": "Database connections reset"}
        else:
            return {"status": "failed", "message": "Failed to reset connections"}
    except Exception as e:
        logger.error(f"Error resetting database: {e}", exc_info=True)
        raise DatabaseOperationError("database connection reset", e)


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
