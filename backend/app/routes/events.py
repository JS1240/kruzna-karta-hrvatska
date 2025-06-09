from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_async_db
from ..models.event import Event
from ..models.schemas import Event as EventSchema
from ..models.schemas import (
    EventCreate,
    EventResponse,
    EventUpdate,
)

router = APIRouter(prefix="/events", tags=["events"])


@router.get("/", response_model=EventResponse)
async def get_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_async_db),
):
    """Get all events with optional filtering and pagination."""
    stmt = select(Event)

    # Apply filters
    if search:
        stmt = stmt.where(
            Event.name.ilike(f"%{search}%") | Event.description.ilike(f"%{search}%")
        )

    if location:
        stmt = stmt.where(Event.location.ilike(f"%{location}%"))

    if date_from:
        stmt = stmt.where(Event.date >= date_from)

    if date_to:
        stmt = stmt.where(Event.date <= date_to)

    total_stmt = select(func.count()).select_from(stmt.subquery())
    result = await db.execute(total_stmt)
    total = result.scalar_one()

    events_result = await db.execute(
        stmt.order_by(Event.date.asc(), Event.time.asc()).offset(skip).limit(limit)
    )
    events = events_result.scalars().all()

    # Calculate pagination info
    pages = (total + limit - 1) // limit if total > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1

    return EventResponse(
        events=events, total=total, page=page, size=len(events), pages=pages
    )


@router.get("/{event_id}", response_model=EventSchema)
async def get_event(event_id: int, db: AsyncSession = Depends(get_async_db)):
    """Get a specific event by ID."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    event = result.scalar_one_or_none()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event


@router.post("/", response_model=EventSchema)
async def create_event(event: EventCreate, db: AsyncSession = Depends(get_async_db)):
    """Create a new event."""
    db_event = Event(**event.model_dump())
    db.add(db_event)
    await db.commit()
    await db.refresh(db_event)
    return db_event


@router.put("/{event_id}", response_model=EventSchema)
async def update_event(
    event_id: int, event: EventUpdate, db: AsyncSession = Depends(get_async_db)
):
    """Update an existing event."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    db_event = result.scalar_one_or_none()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Update only provided fields
    update_data = event.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_event, field, value)

    await db.commit()
    await db.refresh(db_event)
    return db_event


@router.delete("/{event_id}")
async def delete_event(event_id: int, db: AsyncSession = Depends(get_async_db)):
    """Delete an event."""
    result = await db.execute(select(Event).where(Event.id == event_id))
    db_event = result.scalar_one_or_none()
    if not db_event:
        raise HTTPException(status_code=404, detail="Event not found")

    await db.delete(db_event)
    await db.commit()
    return {"message": "Event deleted successfully"}
