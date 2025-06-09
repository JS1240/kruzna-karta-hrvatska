import json
from datetime import date
from typing import Optional

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.cache import get_cache
from ..core.database import get_db
from ..models.event import Event
from ..models.schemas import Event as EventSchema
from ..models.schemas import (
    EventCreate,
    EventResponse,
    EventUpdate,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=EventResponse)
def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    cache=Depends(get_cache),
):
    """Get all events with optional filtering and pagination."""
    cache_key = json.dumps(
        {
            "skip": skip,
            "limit": limit,
            "search": search,
            "location": location,
            "date_from": str(date_from) if date_from else None,
            "date_to": str(date_to) if date_to else None,
        },
        sort_keys=True,
    )

    cached = cache.get(cache_key)
    if cached:
        return EventResponse.model_validate_json(cached)

    query = db.query(Event)

    # Apply filters
    if search:
        query = query.filter(
            Event.search_vector.op("@@")(sa.func.plainto_tsquery("simple", search))
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
    events = (
        query.order_by(Event.date.asc(), Event.time.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # Calculate pagination info
    pages = (total + limit - 1) // limit if total > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1

    response = EventResponse(
        events=events, total=total, page=page, size=len(events), pages=pages
    )

    cache.setex(cache_key, 300, response.model_dump_json())
    return response


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
