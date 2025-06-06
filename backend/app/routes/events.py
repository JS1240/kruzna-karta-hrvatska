from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date

from ..core.database import get_db
from ..models.event import Event
from ..models.schemas import Event as EventSchema, EventCreate, EventUpdate, EventResponse

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=EventResponse)
def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db)
):
    """Get all events with optional filtering and pagination."""
    query = db.query(Event)
    
    # Apply filters
    if search:
        query = query.filter(
            Event.name.ilike(f"%{search}%") | 
            Event.description.ilike(f"%{search}%")
        )
    
    if location:
        query = query.filter(Event.location.ilike(f"%{location}%"))
    
    if date_from:
        query = query.filter(Event.date >= date_from)
    
    if date_to:
        query = query.filter(Event.date <= date_to)
    
    # Get total count
    total = query.count()
    
    # Apply pagination and ordering
    events = query.order_by(Event.date.asc(), Event.time.asc()).offset(skip).limit(limit).all()
    
    # Calculate pagination info
    pages = (total + limit - 1) // limit if total > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return EventResponse(
        events=events,
        total=total,
        page=page,
        size=len(events),
        pages=pages
    )


@router.get("/{event_id}", response_model=EventSchema)
def get_event(event_id: int, db: Session = Depends(get_db)):
    """Get a specific event by ID."""
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/", response_model=EventSchema)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event."""
    db_event = Event(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event


@router.put("/{event_id}", response_model=EventSchema)
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