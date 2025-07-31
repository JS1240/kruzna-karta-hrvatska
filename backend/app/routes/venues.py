from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error_handlers import (
    VenueNotFoundError,
    ResourceAlreadyExistsError,
    CannotDeleteReferencedEntityError
)
from app.models.schemas import Venue as VenueSchema
from app.models.schemas import (
    EventResponse,
    VenueCreate,
    VenueResponse,
    VenueSearchParams,
    VenueUpdate,
)
from app.models.venue import Venue

router = APIRouter(prefix="/venues", tags=["venues"])


@router.get("/", response_model=VenueResponse)
def get_venues(
    q: Optional[str] = Query(None, description="Search venues by name"),
    city: Optional[str] = Query(None, description="Filter by city"),
    venue_type: Optional[str] = Query(None, description="Filter by venue type"),
    latitude: Optional[float] = Query(
        None, description="Latitude for geographic search"
    ),
    longitude: Optional[float] = Query(
        None, description="Longitude for geographic search"
    ),
    radius_km: Optional[float] = Query(None, description="Search radius in kilometers"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db),
) -> VenueResponse:
    """Get venues with comprehensive filtering and geographic search capabilities.
    
    Primary endpoint for retrieving venue information with multiple filter options.
    Supports text search, location-based filtering, venue type classification,
    and geographic proximity search. Results are paginated and sorted
    alphabetically by venue name.
    
    Args:
        q: Optional search query for venue name or address (case-insensitive)
        city: Filter venues by city name (case-insensitive)
        venue_type: Filter by venue type (e.g., "concert_hall", "theater", "stadium")
        latitude: Latitude coordinate for geographic search (requires longitude and radius_km)
        longitude: Longitude coordinate for geographic search (requires latitude and radius_km)
        radius_km: Search radius in kilometers for geographic filtering
        page: Page number for pagination (default: 1, minimum: 1)
        size: Number of venues per page (default: 20, range: 1-100)
        db: Database session dependency (automatically injected)
        
    Returns:
        VenueResponse: Paginated response containing:
            - venues: List of Venue objects with complete details
                (name, address, coordinates, capacity, type, contact info)
            - total: Total number of venues matching filters
            - page: Current page number
            - size: Number of venues returned
            - pages: Total number of pages available
            
    Note:
        Geographic search requires all three parameters: latitude, longitude,
        and radius_km. Uses PostgreSQL earth_distance function for accurate
        geographic calculations.
    """
    query = db.query(Venue)

    # Apply filters
    if q:
        query = query.filter(Venue.name.ilike(f"%{q}%") | Venue.address.ilike(f"%{q}%"))

    if city:
        query = query.filter(Venue.city.ilike(f"%{city}%"))

    if venue_type:
        query = query.filter(Venue.venue_type == venue_type)

    # Geographic filtering
    if latitude is not None and longitude is not None and radius_km is not None:
        # Use PostgreSQL geographic distance calculation
        query = query.filter(
            func.earth_distance(
                func.ll_to_earth(Venue.latitude, Venue.longitude),
                func.ll_to_earth(latitude, longitude),
            )
            <= radius_km * 1000  # Convert km to meters
        )

    # Get total count before pagination
    total = query.count()

    # Calculate pagination
    skip = (page - 1) * size
    pages = (total + size - 1) // size if total > 0 else 0

    # Apply pagination and ordering
    venues = query.order_by(Venue.name.asc()).offset(skip).limit(size).all()

    return VenueResponse(
        venues=venues, total=total, page=page, size=len(venues), pages=pages
    )


@router.get("/search", response_model=VenueResponse)
def search_venues(params: VenueSearchParams = Depends(), db: Session = Depends(get_db)) -> VenueResponse:
    """Advanced venue search with all filters."""
    return get_venues(
        q=params.q,
        city=params.city,
        venue_type=params.venue_type,
        latitude=params.latitude,
        longitude=params.longitude,
        radius_km=params.radius_km,
        page=params.page,
        size=params.size,
        db=db,
    )


@router.get("/cities")
def get_cities(db: Session = Depends(get_db)) -> Dict[str, List[str]]:
    """Get a list of all cities that have registered venues.
    
    Utility endpoint for populating city filter dropdowns in the user interface.
    Returns only cities that actually have venues, sorted alphabetically for
    consistent presentation.
    
    Args:
        db: Database session dependency (automatically injected)
        
    Returns:
        Dict containing:
            - cities: List of city names sorted alphabetically
            
    Note:
        This endpoint performs a DISTINCT query on venue cities, so only
        cities with at least one venue will appear in the results.
    """
    cities = db.query(Venue.city).distinct().order_by(Venue.city.asc()).all()
    return {"cities": [city[0] for city in cities]}


@router.get("/types")
def get_venue_types(db: Session = Depends(get_db)) -> Dict[str, List[str]]:
    """Get a list of all venue types available in the system.
    
    Utility endpoint for populating venue type filter dropdowns in the user
    interface. Returns only types that are actually assigned to venues,
    excluding null values and sorted alphabetically.
    
    Args:
        db: Database session dependency (automatically injected)
        
    Returns:
        Dict containing:
            - types: List of venue type identifiers sorted alphabetically
                (e.g., ["concert_hall", "stadium", "theater"])
                
    Note:
        This endpoint filters out venues with null venue_type values and
        returns only distinct types that are currently in use.
    """
    types = (
        db.query(Venue.venue_type)
        .filter(Venue.venue_type.isnot(None))
        .distinct()
        .order_by(Venue.venue_type.asc())
        .all()
    )
    return {"types": [type_[0] for type_ in types]}


@router.get("/nearby", response_model=VenueResponse)
def get_nearby_venues(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    radius_km: float = Query(10, description="Search radius in kilometers"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> VenueResponse:
    """Get venues near a specific location."""
    return get_venues(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        page=page,
        size=size,
        db=db,
    )


@router.get("/{venue_id}", response_model=VenueSchema)
def get_venue(venue_id: int, db: Session = Depends(get_db)) -> VenueSchema:
    """Get a specific venue by ID.
    
    Args:
        venue_id: Unique identifier of the venue to retrieve
        db: Database session dependency (automatically injected)
        
    Returns:
        VenueSchema: Complete venue object with all details
        
    Raises:
        VenueNotFoundError: If venue with given ID is not found
    """
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise VenueNotFoundError(venue_id)
    return venue


@router.post("/", response_model=VenueSchema)
def create_venue(venue: VenueCreate, db: Session = Depends(get_db)) -> VenueSchema:
    """Create a new venue in the system.
    
    Administrative endpoint for adding new venues. Each venue must have a unique
    name within its city to prevent duplicates and ensure clear identification.
    
    Args:
        venue: VenueCreate object containing venue details:
            - name: Venue name (required, must be unique within city)
            - city: City where venue is located (required)
            - address: Full venue address
            - venue_type: Type classification (e.g., "concert_hall", "theater")
            - capacity: Maximum venue capacity
            - latitude/longitude: Geographic coordinates
        db: Database session dependency (automatically injected)
        
    Returns:
        VenueSchema: The newly created venue with generated ID and timestamps
        
    Raises:
        ResourceAlreadyExistsError: If a venue with the same name already exists in the same city
    """
    # Check if venue with same name and city already exists
    existing = (
        db.query(Venue)
        .filter(Venue.name == venue.name, Venue.city == venue.city)
        .first()
    )
    if existing:
        raise ResourceAlreadyExistsError("Venue", "name", f"{venue.name} in {venue.city}")

    db_venue = Venue(**venue.model_dump())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.put("/{venue_id}", response_model=VenueSchema)
def update_venue(venue_id: int, venue: VenueUpdate, db: Session = Depends(get_db)) -> VenueSchema:
    """Update an existing venue.
    
    Args:
        venue_id: Unique identifier of the venue to update
        venue: VenueUpdate object containing updated venue details
        db: Database session dependency (automatically injected)
        
    Returns:
        VenueSchema: Updated venue object with all details
        
    Raises:
        VenueNotFoundError: If venue with given ID is not found
        ResourceAlreadyExistsError: If venue name conflicts with existing venue in same city
    """
    db_venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not db_venue:
        raise VenueNotFoundError(venue_id)

    # Check for name/city conflicts if those fields are being updated
    update_data = venue.model_dump(exclude_unset=True)
    if "name" in update_data or "city" in update_data:
        new_name = update_data.get("name", db_venue.name)
        new_city = update_data.get("city", db_venue.city)

        existing = (
            db.query(Venue)
            .filter(
                Venue.name == new_name, Venue.city == new_city, Venue.id != venue_id
            )
            .first()
        )
        if existing:
            raise ResourceAlreadyExistsError("Venue", "name", f"{new_name} in {new_city}")

    # Update only provided fields
    for field, value in update_data.items():
        setattr(db_venue, field, value)

    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.delete("/{venue_id}")
def delete_venue(venue_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Delete a venue from the system.
    
    Administrative endpoint for removing venues. Before deletion, the system
    checks if any events are associated with this venue and prevents deletion
    if events exist to maintain data integrity.
    
    Args:
        venue_id: Unique identifier of the venue to delete
        db: Database session dependency (automatically injected)
        
    Returns:
        Dict containing confirmation message:
            - message: "Venue deleted successfully"
            
    Raises:
        VenueNotFoundError: If venue with given ID is not found
        CannotDeleteReferencedEntityError: If venue has associated events and cannot be deleted
    """
    db_venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not db_venue:
        raise VenueNotFoundError(venue_id)

    # Check if venue has events
    from app.models.event import Event

    events_count = db.query(Event).filter(Event.venue_id == venue_id).count()
    if events_count > 0:
        raise CannotDeleteReferencedEntityError("venue", venue_id, events_count, "events")

    db.delete(db_venue)
    db.commit()
    return {"message": "Venue deleted successfully"}


@router.get("/{venue_id}/events")
def get_venue_events(
    venue_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> EventResponse:
    """Get all events scheduled at a specific venue.
    
    Retrieves paginated list of events associated with the specified venue.
    Useful for venue detail pages and venue-specific event listings.
    
    Args:
        venue_id: Unique identifier of the venue
        page: Page number for pagination (default: 1, minimum: 1)
        size: Number of events per page (default: 20, range: 1-100)
        db: Database session dependency (automatically injected)
        
    Returns:
        EventResponse: Paginated response containing:
            - events: List of events at this venue
            - total: Total number of events at this venue
            - page: Current page number
            - size: Number of events returned
            - pages: Total pages available
            
    Raises:
        VenueNotFoundError: If venue with given ID is not found
    """
    # Import here to avoid circular imports
    from app.routes.events import get_events

    # Verify venue exists
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise VenueNotFoundError(venue_id)

    return get_events(venue_id=venue_id, page=page, size=size, db=db)
