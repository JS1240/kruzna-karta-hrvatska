from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List

from ..core.database import get_db
from ..models.venue import Venue
from ..models.schemas import (
    Venue as VenueSchema,
    VenueCreate,
    VenueUpdate,
    VenueResponse,
    VenueSearchParams
)

router = APIRouter(prefix="/venues", tags=["venues"])


@router.get("/", response_model=VenueResponse)
def get_venues(
    q: Optional[str] = Query(None, description="Search venues by name"),
    city: Optional[str] = Query(None, description="Filter by city"),
    venue_type: Optional[str] = Query(None, description="Filter by venue type"),
    latitude: Optional[float] = Query(None, description="Latitude for geographic search"),
    longitude: Optional[float] = Query(None, description="Longitude for geographic search"),
    radius_km: Optional[float] = Query(None, description="Search radius in kilometers"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """Get venues with filtering and geographic search."""
    query = db.query(Venue)
    
    # Apply filters
    if q:
        query = query.filter(
            Venue.name.ilike(f"%{q}%") | 
            Venue.address.ilike(f"%{q}%")
        )
    
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
                func.ll_to_earth(latitude, longitude)
            ) <= radius_km * 1000  # Convert km to meters
        )
    
    # Get total count before pagination
    total = query.count()
    
    # Calculate pagination
    skip = (page - 1) * size
    pages = (total + size - 1) // size if total > 0 else 0
    
    # Apply pagination and ordering
    venues = query.order_by(Venue.name.asc()).offset(skip).limit(size).all()
    
    return VenueResponse(
        venues=venues,
        total=total,
        page=page,
        size=len(venues),
        pages=pages
    )


@router.get("/search", response_model=VenueResponse)
def search_venues(
    params: VenueSearchParams = Depends(),
    db: Session = Depends(get_db)
):
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
        db=db
    )


@router.get("/cities")
def get_cities(db: Session = Depends(get_db)):
    """Get all cities with venues."""
    cities = db.query(Venue.city).distinct().order_by(Venue.city.asc()).all()
    return {"cities": [city[0] for city in cities]}


@router.get("/types")
def get_venue_types(db: Session = Depends(get_db)):
    """Get all venue types."""
    types = db.query(Venue.venue_type).filter(
        Venue.venue_type.isnot(None)
    ).distinct().order_by(Venue.venue_type.asc()).all()
    return {"types": [type_[0] for type_ in types]}


@router.get("/nearby", response_model=VenueResponse)
def get_nearby_venues(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"),
    radius_km: float = Query(10, description="Search radius in kilometers"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get venues near a specific location."""
    return get_venues(
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        page=page,
        size=size,
        db=db
    )


@router.get("/{venue_id}", response_model=VenueSchema)
def get_venue(venue_id: int, db: Session = Depends(get_db)):
    """Get a specific venue by ID."""
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    return venue


@router.post("/", response_model=VenueSchema)
def create_venue(venue: VenueCreate, db: Session = Depends(get_db)):
    """Create a new venue."""
    # Check if venue with same name and city already exists
    existing = db.query(Venue).filter(
        Venue.name == venue.name,
        Venue.city == venue.city
    ).first()
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Venue with this name already exists in this city"
        )
    
    db_venue = Venue(**venue.model_dump())
    db.add(db_venue)
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.put("/{venue_id}", response_model=VenueSchema)
def update_venue(venue_id: int, venue: VenueUpdate, db: Session = Depends(get_db)):
    """Update an existing venue."""
    db_venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not db_venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check for name/city conflicts if those fields are being updated
    update_data = venue.model_dump(exclude_unset=True)
    if 'name' in update_data or 'city' in update_data:
        new_name = update_data.get('name', db_venue.name)
        new_city = update_data.get('city', db_venue.city)
        
        existing = db.query(Venue).filter(
            Venue.name == new_name,
            Venue.city == new_city,
            Venue.id != venue_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Venue with this name already exists in this city"
            )
    
    # Update only provided fields
    for field, value in update_data.items():
        setattr(db_venue, field, value)
    
    db.commit()
    db.refresh(db_venue)
    return db_venue


@router.delete("/{venue_id}")
def delete_venue(venue_id: int, db: Session = Depends(get_db)):
    """Delete a venue."""
    db_venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not db_venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    # Check if venue has events
    from ..models.event import Event
    events_count = db.query(Event).filter(Event.venue_id == venue_id).count()
    if events_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete venue. It has {events_count} associated events."
        )
    
    db.delete(db_venue)
    db.commit()
    return {"message": "Venue deleted successfully"}


@router.get("/{venue_id}/events")
def get_venue_events(
    venue_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get all events for a specific venue."""
    # Import here to avoid circular imports
    from .events import get_events
    
    # Verify venue exists
    venue = db.query(Venue).filter(Venue.id == venue_id).first()
    if not venue:
        raise HTTPException(status_code=404, detail="Venue not found")
    
    return get_events(venue_id=venue_id, page=page, size=size, db=db)