"""
User-generated events API endpoints.
"""

import logging
from datetime import date as Date
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session, joinedload

from ..core.auth import get_current_superuser, get_current_user
from ..core.permissions import require_event_creator
from ..core.database import get_db
from ..models.booking import TicketType
from ..models.category import EventCategory
from ..models.event import Event
from ..models.user import User
from ..models.venue import Venue

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/user-events", tags=["user-events"])


# Pydantic models for request/response
class TicketTypeCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(..., ge=0)
    currency: str = Field(default="EUR", max_length=3)
    total_quantity: int = Field(..., ge=1)
    min_purchase: int = Field(default=1, ge=1)
    max_purchase: int = Field(default=10, ge=1)
    sale_start: Optional[datetime] = None
    sale_end: Optional[datetime] = None

    @validator("max_purchase")
    def validate_max_purchase(cls, v, values):
        if "min_purchase" in values and v < values["min_purchase"]:
            raise ValueError("max_purchase must be >= min_purchase")
        return v


class UserEventCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    description: str = Field(..., min_length=10)
    date: Date = Field(...)
    time: str = Field(..., max_length=50)
    end_date: Optional[Date] = None
    end_time: Optional[str] = Field(None, max_length=50)
    location: str = Field(..., min_length=5, max_length=500)
    category_id: int = Field(...)
    venue_id: Optional[int] = None
    image: Optional[str] = Field(None, max_length=1000)
    link: Optional[str] = Field(None, max_length=1000)
    age_restriction: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None
    ticket_types: List[TicketTypeCreate] = Field(..., min_items=1)

    @validator("date")
    def validate_date(cls, v):
        if v < Date.today():
            raise ValueError("Event date cannot be in the past")
        return v

    @validator("end_date")
    def validate_end_date(cls, v, values):
        if v and "date" in values and v < values["date"]:
            raise ValueError("End date cannot be before start date")
        return v


class UserEventUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = Field(None, min_length=10)
    date: Optional[Date] = None
    time: Optional[str] = Field(None, max_length=50)
    end_date: Optional[Date] = None
    end_time: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, min_length=5, max_length=500)
    category_id: Optional[int] = None
    venue_id: Optional[int] = None
    image: Optional[str] = Field(None, max_length=1000)
    link: Optional[str] = Field(None, max_length=1000)
    age_restriction: Optional[str] = Field(None, max_length=50)
    tags: Optional[List[str]] = None


class EventApprovalUpdate(BaseModel):
    approval_status: str = Field(..., pattern="^(approved|rejected)$")
    admin_notes: Optional[str] = None


# Helper functions
def generate_event_slug(title: str, event_id: int) -> str:
    """Generate a URL-friendly slug for the event"""
    import re

    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[-\s]+", "-", slug)
    return f"{slug}-{event_id}"


# Routes
@router.post("/create", status_code=status.HTTP_201_CREATED)
def create_user_event(
    event_data: UserEventCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new user-generated event."""
    try:
        require_event_creator(
            current_user,
            "You need to be a venue owner or manager to create events. Please contact support to upgrade your account.",
        )

        # Validate category exists
        category = (
            db.query(EventCategory)
            .filter(EventCategory.id == event_data.category_id)
            .first()
        )
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid category ID"
            )

        # Validate venue if provided
        if event_data.venue_id:
            venue = db.query(Venue).filter(Venue.id == event_data.venue_id).first()
            if not venue:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid venue ID"
                )

        # Create the event
        event = Event(
            title=event_data.title,
            description=event_data.description,
            date=event_data.date,
            time=event_data.time,
            end_date=event_data.end_date,
            end_time=event_data.end_time,
            location=event_data.location,
            category_id=event_data.category_id,
            venue_id=event_data.venue_id,
            image=event_data.image,
            link=event_data.link,
            age_restriction=event_data.age_restriction,
            tags=event_data.tags or [],
            organizer_id=current_user.id,
            source="user_generated",
            is_user_generated=True,
            approval_status="pending",
            event_status="draft",
            is_featured=False,
        )

        db.add(event)
        db.flush()  # Get event ID

        # Generate slug
        event.slug = generate_event_slug(event_data.title, event.id)

        # Create ticket types
        for ticket_data in event_data.ticket_types:
            ticket_type = TicketType(
                event_id=event.id,
                name=ticket_data.name,
                description=ticket_data.description,
                price=ticket_data.price,
                currency=ticket_data.currency,
                total_quantity=ticket_data.total_quantity,
                available_quantity=ticket_data.total_quantity,
                min_purchase=ticket_data.min_purchase,
                max_purchase=ticket_data.max_purchase,
                sale_start=ticket_data.sale_start,
                sale_end=ticket_data.sale_end,
            )
            db.add(ticket_type)

        db.commit()
        db.refresh(event)

        logger.info(f"User {current_user.id} created event {event.id}: {event.title}")

        return {
            "message": "Event created successfully and submitted for review!",
            "event": {
                "id": event.id,
                "title": event.title,
                "slug": event.slug,
                "approval_status": event.approval_status,
                "created_at": event.created_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating user event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event. Please try again.",
        )


@router.get("/my-events")
def get_my_events(
    status_filter: Optional[str] = Query(None, description="Filter by approval status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all events created by the current user."""
    try:
        query = (
            db.query(Event)
            .options(
                joinedload(Event.category),
                joinedload(Event.venue),
                joinedload(Event.ticket_types),
            )
            .filter(Event.organizer_id == current_user.id)
        )

        if status_filter:
            if status_filter not in ["pending", "approved", "rejected"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid status filter. Use: pending, approved, rejected",
                )
            query = query.filter(Event.approval_status == status_filter)

        # Get total count and apply pagination
        total = query.count()
        skip = (page - 1) * size
        pages = (total + size - 1) // size if total > 0 else 0

        events = query.order_by(Event.created_at.desc()).offset(skip).limit(size).all()

        # Format response
        event_list = []
        for event in events:
            event_list.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "date": event.date.isoformat() if event.date else None,
                    "time": event.time,
                    "location": event.location,
                    "approval_status": event.approval_status,
                    "event_status": event.event_status,
                    "category": (
                        {"id": event.category.id, "name": event.category.name}
                        if event.category
                        else None
                    ),
                    "venue": (
                        {"id": event.venue.id, "name": event.venue.name}
                        if event.venue
                        else None
                    ),
                    "ticket_types_count": len(event.ticket_types),
                    "view_count": event.view_count or 0,
                    "created_at": event.created_at.isoformat(),
                }
            )

        return {
            "events": event_list,
            "total": total,
            "page": page,
            "size": len(event_list),
            "pages": pages,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve events",
        )


@router.get("/{event_id}")
def get_user_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific event created by the current user."""
    try:
        event = (
            db.query(Event)
            .options(
                joinedload(Event.category),
                joinedload(Event.venue),
                joinedload(Event.ticket_types),
            )
            .filter(Event.id == event_id, Event.organizer_id == current_user.id)
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found or you don't have permission to view it",
            )

        return {
            "id": event.id,
            "title": event.title,
            "description": event.description,
            "date": event.date.isoformat() if event.date else None,
            "time": event.time,
            "end_date": event.end_date.isoformat() if event.end_date else None,
            "end_time": event.end_time,
            "location": event.location,
            "image": event.image,
            "link": event.link,
            "age_restriction": event.age_restriction,
            "tags": event.tags or [],
            "approval_status": event.approval_status,
            "event_status": event.event_status,
            "platform_commission_rate": float(event.platform_commission_rate),
            "category": (
                {"id": event.category.id, "name": event.category.name}
                if event.category
                else None
            ),
            "venue": (
                {"id": event.venue.id, "name": event.venue.name}
                if event.venue
                else None
            ),
            "ticket_types": [
                {
                    "id": tt.id,
                    "name": tt.name,
                    "description": tt.description,
                    "price": float(tt.price),
                    "currency": tt.currency,
                    "total_quantity": tt.total_quantity,
                    "available_quantity": tt.available_quantity,
                    "min_purchase": tt.min_purchase,
                    "max_purchase": tt.max_purchase,
                    "sale_start": tt.sale_start.isoformat() if tt.sale_start else None,
                    "sale_end": tt.sale_end.isoformat() if tt.sale_end else None,
                }
                for tt in event.ticket_types
            ],
            "view_count": event.view_count or 0,
            "created_at": event.created_at.isoformat(),
            "updated_at": event.updated_at.isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving user event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event",
        )


@router.put("/{event_id}")
def update_user_event(
    event_id: int,
    event_data: UserEventUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a user-generated event (only if pending or rejected)."""
    try:
        event = (
            db.query(Event)
            .filter(Event.id == event_id, Event.organizer_id == current_user.id)
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found or you don't have permission to edit it",
            )

        # Can only edit pending or rejected events
        if event.approval_status == "approved":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot edit approved events. Please contact support for changes.",
            )

        # Update fields
        update_data = event_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(event, field):
                setattr(event, field, value)

        # If event was rejected and now being updated, reset to pending
        if event.approval_status == "rejected":
            event.approval_status = "pending"

        # Update slug if title changed
        if "title" in update_data:
            event.slug = generate_event_slug(event_data.title, event.id)

        db.commit()
        db.refresh(event)

        logger.info(f"User {current_user.id} updated event {event.id}")

        return {
            "message": "Event updated successfully!",
            "event": {
                "id": event.id,
                "title": event.title,
                "approval_status": event.approval_status,
                "updated_at": event.updated_at.isoformat(),
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating user event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event",
        )


@router.delete("/{event_id}")
def delete_user_event(
    event_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a user-generated event (only if pending or rejected)."""
    try:
        event = (
            db.query(Event)
            .filter(Event.id == event_id, Event.organizer_id == current_user.id)
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found or you don't have permission to delete it",
            )

        # Can only delete pending or rejected events, or if no bookings exist
        from ..models.booking import Booking

        booking_count = db.query(Booking).filter(Booking.event_id == event.id).count()

        if event.approval_status == "approved" and booking_count > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete approved events with existing bookings. Please contact support.",
            )

        db.delete(event)
        db.commit()

        logger.info(f"User {current_user.id} deleted event {event.id}")

        return {"message": "Event deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting user event {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete event",
        )


# Admin routes
@router.get("/admin/pending")
def get_pending_events(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=200, description="Page size"),
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """Get all pending events for admin review."""
    try:
        query = (
            db.query(Event)
            .options(
                joinedload(Event.category),
                joinedload(Event.venue),
                joinedload(Event.event_organizer),
            )
            .filter(Event.is_user_generated == True, Event.approval_status == "pending")
        )

        # Get total count and apply pagination
        total = query.count()
        skip = (page - 1) * size
        pages = (total + size - 1) // size if total > 0 else 0

        events = query.order_by(Event.created_at.asc()).offset(skip).limit(size).all()

        # Format response
        event_list = []
        for event in events:
            event_list.append(
                {
                    "id": event.id,
                    "title": event.title,
                    "description": (
                        event.description[:200] + "..."
                        if len(event.description) > 200
                        else event.description
                    ),
                    "date": event.date.isoformat() if event.date else None,
                    "time": event.time,
                    "location": event.location,
                    "category": (
                        {"id": event.category.id, "name": event.category.name}
                        if event.category
                        else None
                    ),
                    "organizer": (
                        {
                            "id": event.event_organizer.id,
                            "email": event.event_organizer.email,
                            "name": f"{event.event_organizer.first_name} {event.event_organizer.last_name}".strip(),
                        }
                        if event.event_organizer
                        else None
                    ),
                    "created_at": event.created_at.isoformat(),
                }
            )

        return {
            "events": event_list,
            "total": total,
            "page": page,
            "size": len(event_list),
            "pages": pages,
        }

    except Exception as e:
        logger.error(f"Error retrieving pending events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending events",
        )


@router.put("/admin/{event_id}/approve")
def update_event_approval(
    event_id: int,
    approval_data: EventApprovalUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """Approve or reject a pending user event."""
    try:
        event = (
            db.query(Event)
            .filter(Event.id == event_id, Event.is_user_generated == True)
            .first()
        )

        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User-generated event not found",
            )

        if event.approval_status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Event is already {event.approval_status}",
            )

        # Update approval status
        event.approval_status = approval_data.approval_status

        # If approved, make the event active
        if approval_data.approval_status == "approved":
            event.event_status = "active"

        # TODO: Add admin notes field to events table for rejection reasons
        # event.admin_notes = approval_data.admin_notes

        db.commit()
        db.refresh(event)

        logger.info(
            f"Admin {current_user.id} {approval_data.approval_status} event {event.id}"
        )

        # TODO: Send notification to event organizer

        return {
            "message": f"Event {approval_data.approval_status} successfully",
            "event": {
                "id": event.id,
                "title": event.title,
                "approval_status": event.approval_status,
                "event_status": event.event_status,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating event approval {event_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event approval",
        )


@router.get("/stats/organizer")
def get_organizer_stats(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get statistics for the current organizer."""
    try:
        require_event_creator(current_user)

        # Get event statistics
        total_events = (
            db.query(Event).filter(Event.organizer_id == current_user.id).count()
        )
        pending_events = (
            db.query(Event)
            .filter(
                Event.organizer_id == current_user.id,
                Event.approval_status == "pending",
            )
            .count()
        )
        approved_events = (
            db.query(Event)
            .filter(
                Event.organizer_id == current_user.id,
                Event.approval_status == "approved",
            )
            .count()
        )
        rejected_events = (
            db.query(Event)
            .filter(
                Event.organizer_id == current_user.id,
                Event.approval_status == "rejected",
            )
            .count()
        )

        # Get booking statistics
        from sqlalchemy import func

        from ..models.booking import Booking

        booking_stats = (
            db.query(
                func.count(Booking.id).label("total_bookings"),
                func.sum(Booking.total_price).label("total_revenue"),
                func.sum(Booking.platform_commission_amount).label("total_commission"),
                func.sum(Booking.organizer_revenue).label("total_organizer_revenue"),
            )
            .join(Event)
            .filter(Event.organizer_id == current_user.id)
            .first()
        )

        total_bookings = booking_stats.total_bookings or 0
        total_revenue = float(booking_stats.total_revenue or 0)
        platform_commission = float(booking_stats.total_commission or 0)
        organizer_revenue = float(booking_stats.total_organizer_revenue or 0)

        return {
            "events": {
                "total": total_events,
                "pending": pending_events,
                "approved": approved_events,
                "rejected": rejected_events,
            },
            "bookings": {
                "total_bookings": total_bookings,
                "total_revenue": total_revenue,
                "platform_commission": platform_commission,
                "organizer_revenue": organizer_revenue,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving organizer stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics",
        )


@router.get("/analytics/revenue-trends")
def get_revenue_trends(
    period: str = Query("month", pattern="^(week|month|quarter|year)$"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get revenue trends over time for the organizer."""
    try:
        require_event_creator(current_user)

        from sqlalchemy import extract, func

        from ..models.booking import Booking

        # Define date grouping based on period
        if period == "week":
            date_trunc = func.date_trunc("week", Booking.booking_date)
            interval = func.extract("week", Booking.booking_date)
            year_part = func.extract("year", Booking.booking_date)
        elif period == "month":
            date_trunc = func.date_trunc("month", Booking.booking_date)
            interval = func.extract("month", Booking.booking_date)
            year_part = func.extract("year", Booking.booking_date)
        elif period == "quarter":
            date_trunc = func.date_trunc("quarter", Booking.booking_date)
            interval = func.extract("quarter", Booking.booking_date)
            year_part = func.extract("year", Booking.booking_date)
        else:  # year
            date_trunc = func.date_trunc("year", Booking.booking_date)
            interval = func.extract("year", Booking.booking_date)
            year_part = func.extract("year", Booking.booking_date)

        trends = (
            db.query(
                date_trunc.label("period"),
                func.sum(Booking.total_price).label("total_revenue"),
                func.sum(Booking.platform_commission_amount).label("commission"),
                func.sum(Booking.organizer_revenue).label("organizer_revenue"),
                func.count(Booking.id).label("booking_count"),
            )
            .join(Event)
            .filter(Event.organizer_id == current_user.id)
            .group_by(date_trunc)
            .order_by(date_trunc)
            .all()
        )

        return {
            "period": period,
            "trends": [
                {
                    "period": trend.period.isoformat() if trend.period else None,
                    "total_revenue": float(trend.total_revenue or 0),
                    "commission": float(trend.commission or 0),
                    "organizer_revenue": float(trend.organizer_revenue or 0),
                    "booking_count": trend.booking_count,
                }
                for trend in trends
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving revenue trends: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve revenue trends",
        )


@router.get("/analytics/event-performance")
def get_event_performance(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get performance breakdown by event for the organizer."""
    try:
        require_event_creator(current_user)

        from sqlalchemy import func

        from ..models.booking import Booking

        event_performance = (
            db.query(
                Event.id,
                Event.title,
                Event.date,
                Event.location,
                func.count(Booking.id).label("total_bookings"),
                func.sum(Booking.total_price).label("total_revenue"),
                func.sum(Booking.platform_commission_amount).label("commission"),
                func.sum(Booking.organizer_revenue).label("organizer_revenue"),
                func.sum(Booking.quantity).label("tickets_sold"),
                Event.view_count,
            )
            .outerjoin(Booking)
            .filter(Event.organizer_id == current_user.id)
            .group_by(Event.id)
            .order_by(func.sum(Booking.total_price).desc().nullslast())
            .all()
        )

        return {
            "events": [
                {
                    "event_id": event.id,
                    "title": event.title,
                    "date": event.date.isoformat(),
                    "location": event.location,
                    "total_bookings": event.total_bookings or 0,
                    "total_revenue": float(event.total_revenue or 0),
                    "commission": float(event.commission or 0),
                    "organizer_revenue": float(event.organizer_revenue or 0),
                    "tickets_sold": event.tickets_sold or 0,
                    "view_count": event.view_count or 0,
                    "conversion_rate": round(
                        (event.total_bookings or 0)
                        / max(event.view_count or 1, 1)
                        * 100,
                        2,
                    ),
                }
                for event in event_performance
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving event performance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event performance",
        )


@router.get("/analytics/ticket-types")
def get_ticket_type_analytics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get analytics breakdown by ticket types for the organizer."""
    try:
        require_event_creator(current_user)

        from sqlalchemy import func

        from ..models.booking import Booking, TicketType

        ticket_analytics = (
            db.query(
                TicketType.name,
                TicketType.price,
                func.count(Booking.id).label("total_bookings"),
                func.sum(Booking.quantity).label("tickets_sold"),
                func.sum(Booking.total_price).label("total_revenue"),
                func.sum(Booking.organizer_revenue).label("organizer_revenue"),
                TicketType.total_quantity,
                TicketType.available_quantity,
            )
            .join(Booking)
            .join(Event)
            .filter(Event.organizer_id == current_user.id)
            .group_by(TicketType.id)
            .order_by(func.sum(Booking.total_price).desc())
            .all()
        )

        return {
            "ticket_types": [
                {
                    "name": ticket.name,
                    "price": float(ticket.price),
                    "total_bookings": ticket.total_bookings,
                    "tickets_sold": ticket.tickets_sold,
                    "total_revenue": float(ticket.total_revenue or 0),
                    "organizer_revenue": float(ticket.organizer_revenue or 0),
                    "total_quantity": ticket.total_quantity,
                    "available_quantity": ticket.available_quantity,
                    "sold_percentage": round(
                        (ticket.tickets_sold or 0)
                        / max(ticket.total_quantity, 1)
                        * 100,
                        2,
                    ),
                }
                for ticket in ticket_analytics
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ticket type analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket type analytics",
        )


@router.get("/analytics/booking-conversion")
def get_booking_conversion_metrics(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get booking conversion metrics for the organizer."""
    try:
        require_event_creator(current_user)

        from sqlalchemy import func

        from ..models.booking import Booking

        # Get total views and bookings
        total_views = (
            db.query(func.sum(Event.view_count))
            .filter(Event.organizer_id == current_user.id)
            .scalar()
            or 0
        )

        total_bookings = (
            db.query(func.count(Booking.id))
            .join(Event)
            .filter(Event.organizer_id == current_user.id)
            .scalar()
            or 0
        )

        # Get conversion by event status
        conversions_by_status = (
            db.query(
                Event.event_status,
                func.sum(Event.view_count).label("total_views"),
                func.count(Booking.id).label("total_bookings"),
            )
            .outerjoin(Booking)
            .filter(Event.organizer_id == current_user.id)
            .group_by(Event.event_status)
            .all()
        )

        return {
            "overall_conversion_rate": round(
                total_bookings / max(total_views, 1) * 100, 2
            ),
            "total_views": total_views,
            "total_bookings": total_bookings,
            "conversion_by_status": [
                {
                    "status": conv.event_status,
                    "views": conv.total_views or 0,
                    "bookings": conv.total_bookings or 0,
                    "conversion_rate": round(
                        (conv.total_bookings or 0)
                        / max(conv.total_views or 1, 1)
                        * 100,
                        2,
                    ),
                }
                for conv in conversions_by_status
            ],
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving booking conversion metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve booking conversion metrics",
        )


@router.get("/analytics/geographic-revenue")
def get_geographic_revenue(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get revenue distribution by location for the organizer."""
    try:
        require_event_creator(current_user)

        from sqlalchemy import func

        from ..models.booking import Booking

        geographic_revenue = (
            db.query(
                Event.location,
                func.count(Booking.id).label("total_bookings"),
                func.sum(Booking.total_price).label("total_revenue"),
                func.sum(Booking.organizer_revenue).label("organizer_revenue"),
                func.count(Event.id.distinct()).label("event_count"),
            )
            .outerjoin(Booking)
            .filter(Event.organizer_id == current_user.id)
            .group_by(Event.location)
            .order_by(func.sum(Booking.total_price).desc().nullslast())
            .all()
        )

        return {
            "locations": [
                {
                    "location": location.location,
                    "event_count": location.event_count,
                    "total_bookings": location.total_bookings or 0,
                    "total_revenue": float(location.total_revenue or 0),
                    "organizer_revenue": float(location.organizer_revenue or 0),
                    "avg_revenue_per_event": round(
                        float(location.total_revenue or 0)
                        / max(location.event_count, 1),
                        2,
                    ),
                }
                for location in geographic_revenue
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving geographic revenue: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve geographic revenue",
        )
