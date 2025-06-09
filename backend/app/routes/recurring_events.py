"""
Recurring events and event series API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import date, datetime
import logging

from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.recurring_events import get_recurring_events_service, RecurringEventsServiceError
from ..models.user import User
from ..models.recurring_events import RecurrencePattern, RecurrenceEndType, SeriesStatus, EventInstanceStatus
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/recurring-events", tags=["recurring-events"])


# Pydantic models for request/response
class SeriesCreateRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=500)
    description: Optional[str] = None
    category_id: Optional[int] = None
    venue_id: Optional[int] = None
    
    # Template configuration
    template_title: Optional[str] = Field(None, max_length=500)
    template_description: Optional[str] = None
    template_price: Optional[str] = None
    template_image: Optional[str] = None
    template_tags: Optional[List[str]] = None
    
    # Timing
    start_date: date
    start_time: Optional[str] = Field(None, max_length=50)
    duration_minutes: Optional[int] = Field(60, ge=15, le=1440)
    
    # Recurrence
    recurrence_pattern: RecurrencePattern
    recurrence_interval: Optional[int] = Field(1, ge=1, le=52)
    recurrence_end_type: Optional[RecurrenceEndType] = RecurrenceEndType.NEVER
    recurrence_end_date: Optional[date] = None
    max_occurrences: Optional[int] = Field(None, ge=1, le=1000)
    recurrence_days: Optional[List[int]] = Field(None, description="0=Monday, 6=Sunday")
    
    # Configuration
    auto_publish: Optional[bool] = False
    advance_notice_days: Optional[int] = Field(30, ge=7, le=365)


class SeriesUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = None
    template_title: Optional[str] = Field(None, max_length=500)
    template_description: Optional[str] = None
    template_price: Optional[str] = None
    template_image: Optional[str] = None
    template_tags: Optional[List[str]] = None
    
    # Application scope
    apply_to_future: Optional[bool] = True
    apply_to_existing: Optional[bool] = False


class InstanceModifyRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=500)
    description: Optional[str] = None
    price: Optional[str] = None
    image: Optional[str] = None
    location: Optional[str] = None
    scheduled_date: Optional[date] = None
    scheduled_time: Optional[str] = Field(None, max_length=50)


@router.post("/series/create")
def create_event_series(
    series_request: SeriesCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new recurring event series."""
    try:
        recurring_service = get_recurring_events_service()
        
        result = recurring_service.create_event_series(
            db=db,
            organizer_id=current_user.id,
            series_data=series_request.model_dump()
        )
        
        return result
        
    except RecurringEventsServiceError as e:
        logger.error(f"Recurring events service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in create_event_series: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create event series"
        )


@router.get("/series/{series_id}")
def get_event_series(
    series_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get event series details."""
    try:
        from ..models.recurring_events import EventSeries
        from sqlalchemy.orm import joinedload
        
        series = db.query(EventSeries).options(
            joinedload(EventSeries.organizer),
            joinedload(EventSeries.category),
            joinedload(EventSeries.venue)
        ).filter(EventSeries.id == series_id).first()
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event series not found"
            )
        
        # Check if user has access (organizer or admin)
        if series.organizer_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return {
            "id": series.id,
            "title": series.title,
            "description": series.description,
            "organizer": {
                "id": series.organizer.id,
                "username": series.organizer.username,
                "email": series.organizer.email
            } if series.organizer else None,
            "category": {
                "id": series.category.id,
                "name": series.category.name
            } if series.category else None,
            "venue": {
                "id": series.venue.id,
                "name": series.venue.name,
                "location": series.venue.location
            } if series.venue else None,
            "series_status": series.series_status.value,
            "template": {
                "title": series.template_title,
                "description": series.template_description,
                "price": series.template_price,
                "image": series.template_image,
                "tags": series.template_tags
            },
            "timing": {
                "start_date": series.start_date.isoformat(),
                "start_time": series.start_time,
                "duration_minutes": series.duration_minutes,
                "timezone": series.timezone
            },
            "recurrence": {
                "pattern": series.recurrence_pattern.value,
                "interval": series.recurrence_interval,
                "end_type": series.recurrence_end_type.value,
                "end_date": series.recurrence_end_date.isoformat() if series.recurrence_end_date else None,
                "max_occurrences": series.max_occurrences,
                "days": series.recurrence_days
            },
            "configuration": {
                "auto_publish": series.auto_publish,
                "advance_notice_days": series.advance_notice_days
            },
            "statistics": {
                "total_instances": series.total_instances,
                "published_instances": series.published_instances,
                "completed_instances": series.completed_instances
            },
            "created_at": series.created_at.isoformat(),
            "updated_at": series.updated_at.isoformat(),
            "last_generated_at": series.last_generated_at.isoformat() if series.last_generated_at else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_event_series: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event series"
        )


@router.put("/series/{series_id}")
def update_event_series(
    series_id: int,
    update_request: SeriesUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an event series."""
    try:
        # Verify series ownership
        from ..models.recurring_events import EventSeries
        series = db.query(EventSeries).filter(EventSeries.id == series_id).first()
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event series not found"
            )
        
        if series.organizer_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        recurring_service = get_recurring_events_service()
        
        # Extract application scope settings
        apply_to_future = update_request.apply_to_future
        apply_to_existing = update_request.apply_to_existing
        
        # Remove scope settings from update data
        update_data = update_request.model_dump(exclude_unset=True)
        update_data.pop('apply_to_future', None)
        update_data.pop('apply_to_existing', None)
        
        result = recurring_service.update_series(
            db=db,
            series_id=series_id,
            update_data=update_data,
            user_id=current_user.id,
            apply_to_future=apply_to_future,
            apply_to_existing=apply_to_existing
        )
        
        return result
        
    except RecurringEventsServiceError as e:
        logger.error(f"Recurring events service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_event_series: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update event series"
        )


@router.get("/series/{series_id}/instances")
def get_series_instances(
    series_id: int,
    status_filter: Optional[str] = Query(None, description="Filter by instance status"),
    date_from: Optional[date] = Query(None, description="Filter instances from date"),
    date_to: Optional[date] = Query(None, description="Filter instances to date"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get instances for an event series."""
    try:
        # Verify series access
        from ..models.recurring_events import EventSeries
        series = db.query(EventSeries).filter(EventSeries.id == series_id).first()
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event series not found"
            )
        
        if series.organizer_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        recurring_service = get_recurring_events_service()
        
        result = recurring_service.get_series_instances(
            db=db,
            series_id=series_id,
            status_filter=status_filter,
            date_from=date_from,
            date_to=date_to,
            page=page,
            size=size
        )
        
        return result
        
    except RecurringEventsServiceError as e:
        logger.error(f"Recurring events service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_series_instances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve series instances"
        )


@router.put("/instances/{instance_id}")
def modify_event_instance(
    instance_id: int,
    modify_request: InstanceModifyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Modify a specific event instance."""
    try:
        # Verify instance ownership
        from ..models.recurring_events import EventInstance, EventSeries
        instance = db.query(EventInstance).join(EventSeries).filter(
            EventInstance.id == instance_id
        ).first()
        
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event instance not found"
            )
        
        if instance.series.organizer_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        recurring_service = get_recurring_events_service()
        
        result = recurring_service.modify_instance(
            db=db,
            instance_id=instance_id,
            modification_data=modify_request.model_dump(exclude_unset=True),
            user_id=current_user.id
        )
        
        return result
        
    except RecurringEventsServiceError as e:
        logger.error(f"Recurring events service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in modify_event_instance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to modify event instance"
        )


@router.post("/instances/{instance_id}/cancel")
def cancel_event_instance(
    instance_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a specific event instance."""
    try:
        # Verify instance ownership
        from ..models.recurring_events import EventInstance, EventSeries
        instance = db.query(EventInstance).join(EventSeries).filter(
            EventInstance.id == instance_id
        ).first()
        
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event instance not found"
            )
        
        if instance.series.organizer_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        recurring_service = get_recurring_events_service()
        
        result = recurring_service.cancel_instance(
            db=db,
            instance_id=instance_id,
            user_id=current_user.id,
            reason=reason
        )
        
        return result
        
    except RecurringEventsServiceError as e:
        logger.error(f"Recurring events service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in cancel_event_instance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel event instance"
        )


@router.post("/instances/{instance_id}/publish")
def publish_event_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish a scheduled event instance."""
    try:
        # Verify instance ownership
        from ..models.recurring_events import EventInstance, EventSeries
        instance = db.query(EventInstance).join(EventSeries).filter(
            EventInstance.id == instance_id
        ).first()
        
        if not instance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event instance not found"
            )
        
        if instance.series.organizer_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        if instance.instance_status != EventInstanceStatus.SCHEDULED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot publish instance with status: {instance.instance_status.value}"
            )
        
        recurring_service = get_recurring_events_service()
        
        # Publish the instance
        recurring_service._publish_instance(db, instance)
        
        db.commit()
        
        return {
            "status": "success",
            "instance_id": instance_id,
            "event_id": instance.event_id,
            "published_at": instance.published_at.isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in publish_event_instance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish event instance"
        )


@router.get("/my-series")
def get_my_event_series(
    status_filter: Optional[str] = Query(None, description="Filter by series status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's event series."""
    try:
        from ..models.recurring_events import EventSeries
        from sqlalchemy.orm import joinedload
        
        query = db.query(EventSeries).options(
            joinedload(EventSeries.category),
            joinedload(EventSeries.venue)
        ).filter(EventSeries.organizer_id == current_user.id)
        
        # Apply status filter
        if status_filter:
            try:
                status_enum = SeriesStatus(status_filter)
                query = query.filter(EventSeries.series_status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        # Get total count and apply pagination
        total = query.count()
        skip = (page - 1) * size
        pages = (total + size - 1) // size if total > 0 else 0
        
        series_list = query.order_by(EventSeries.created_at.desc()).offset(skip).limit(size).all()
        
        # Format response
        formatted_series = []
        for series in series_list:
            formatted_series.append({
                "id": series.id,
                "title": series.title,
                "series_status": series.series_status.value,
                "recurrence_pattern": series.recurrence_pattern.value,
                "recurrence_interval": series.recurrence_interval,
                "start_date": series.start_date.isoformat(),
                "category": {
                    "id": series.category.id,
                    "name": series.category.name
                } if series.category else None,
                "venue": {
                    "id": series.venue.id,
                    "name": series.venue.name
                } if series.venue else None,
                "statistics": {
                    "total_instances": series.total_instances,
                    "published_instances": series.published_instances,
                    "completed_instances": series.completed_instances
                },
                "created_at": series.created_at.isoformat(),
                "last_generated_at": series.last_generated_at.isoformat() if series.last_generated_at else None
            })
        
        return {
            "series": formatted_series,
            "total": total,
            "page": page,
            "size": len(formatted_series),
            "pages": pages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_my_event_series: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve event series"
        )


@router.get("/upcoming-instances")
def get_upcoming_instances(
    days_ahead: int = Query(30, ge=1, le=365, description="Days ahead to look"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of instances"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get upcoming event instances for current user."""
    try:
        recurring_service = get_recurring_events_service()
        
        instances = recurring_service.get_upcoming_instances(
            db=db,
            user_id=current_user.id,
            days_ahead=days_ahead,
            limit=limit
        )
        
        return {
            "upcoming_instances": instances,
            "count": len(instances),
            "days_ahead": days_ahead
        }
        
    except Exception as e:
        logger.error(f"Unexpected error in get_upcoming_instances: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve upcoming instances"
        )


@router.get("/series/{series_id}/statistics")
def get_series_statistics(
    series_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get comprehensive statistics for an event series."""
    try:
        # Verify series access
        from ..models.recurring_events import EventSeries
        series = db.query(EventSeries).filter(EventSeries.id == series_id).first()
        
        if not series:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event series not found"
            )
        
        if series.organizer_id != current_user.id and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        recurring_service = get_recurring_events_service()
        
        statistics = recurring_service.generate_series_statistics(db=db, series_id=series_id)
        
        return statistics
        
    except RecurringEventsServiceError as e:
        logger.error(f"Recurring events service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_series_statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve series statistics"
        )


@router.get("/patterns")
def get_recurrence_patterns():
    """Get available recurrence patterns."""
    return {
        "patterns": [
            {
                "value": pattern.value,
                "name": pattern.value.replace("_", " ").title(),
                "description": _get_pattern_description(pattern)
            }
            for pattern in RecurrencePattern
        ]
    }


def _get_pattern_description(pattern: RecurrencePattern) -> str:
    """Get description for recurrence pattern."""
    descriptions = {
        RecurrencePattern.DAILY: "Repeats every day",
        RecurrencePattern.WEEKLY: "Repeats on specific days of the week",
        RecurrencePattern.BIWEEKLY: "Repeats every two weeks",
        RecurrencePattern.MONTHLY: "Repeats monthly on the same date",
        RecurrencePattern.YEARLY: "Repeats yearly on the same date",
        RecurrencePattern.CUSTOM: "Custom recurrence pattern"
    }
    return descriptions.get(pattern, "Custom recurrence pattern")