"""
Event booking and ticketing API endpoints.
"""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..core.database import get_db
from ..core.auth import get_current_user
from ..core.booking import get_booking_service, BookingServiceError
from ..models.user import User
from ..models.booking import PaymentMethod, BookingStatus, TicketStatus
from pydantic import BaseModel, EmailStr, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/booking", tags=["booking"])


# Pydantic models for request/response
class CustomerInfo(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)


class BookingRequest(BaseModel):
    event_id: int
    ticket_type_id: int
    quantity: int = Field(..., ge=1, le=20)
    customer_info: CustomerInfo
    payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD


class BookingResponse(BaseModel):
    status: str
    booking: Optional[Dict[str, Any]] = None
    payment: Optional[Dict[str, Any]] = None
    tickets: Optional[List[Dict[str, Any]]] = None
    message: Optional[str] = None


class TicketValidationRequest(BaseModel):
    ticket_number: str
    validation_location: Optional[str] = None


@router.post("/create", response_model=BookingResponse)
def create_booking(
    booking_request: BookingRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new event booking."""
    try:
        booking_service = get_booking_service()
        
        result = booking_service.create_booking(
            db=db,
            user_id=current_user.id,
            event_id=booking_request.event_id,
            ticket_type_id=booking_request.ticket_type_id,
            quantity=booking_request.quantity,
            customer_info=booking_request.customer_info.model_dump(),
            payment_method=booking_request.payment_method
        )
        
        return BookingResponse(**result)
        
    except BookingServiceError as e:
        logger.error(f"Booking service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in create_booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create booking"
        )


@router.get("/{booking_reference}")
def get_booking(
    booking_reference: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get booking details by reference."""
    try:
        booking_service = get_booking_service()
        
        result = booking_service.get_booking(
            db=db,
            booking_reference=booking_reference,
            user_id=current_user.id
        )
        
        return result
        
    except BookingServiceError as e:
        logger.error(f"Booking service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve booking"
        )


@router.get("/user/bookings")
def get_user_bookings(
    status_filter: Optional[str] = Query(None, description="Filter by booking status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bookings for the current user."""
    try:
        from ..models.booking import Booking
        from sqlalchemy.orm import joinedload
        
        query = db.query(Booking).options(
            joinedload(Booking.event),
            joinedload(Booking.ticket_type)
        ).filter(Booking.user_id == current_user.id)
        
        if status_filter:
            try:
                status_enum = BookingStatus(status_filter)
                query = query.filter(Booking.booking_status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        # Get total count and apply pagination
        total = query.count()
        skip = (page - 1) * size
        pages = (total + size - 1) // size if total > 0 else 0
        
        bookings = query.order_by(Booking.booking_date.desc()).offset(skip).limit(size).all()
        
        # Format response
        booking_list = []
        for booking in bookings:
            booking_list.append({
                "id": booking.id,
                "booking_reference": booking.booking_reference,
                "status": booking.booking_status.value,
                "event": {
                    "id": booking.event.id,
                    "title": booking.event.title,
                    "date": booking.event.date.isoformat() if booking.event.date else None,
                    "location": booking.event.location
                } if booking.event else None,
                "ticket_type": {
                    "name": booking.ticket_type.name,
                    "price": float(booking.ticket_type.price)
                } if booking.ticket_type else None,
                "quantity": booking.quantity,
                "total_price": float(booking.total_price),
                "currency": booking.currency,
                "booking_date": booking.booking_date.isoformat(),
                "confirmation_date": booking.confirmation_date.isoformat() if booking.confirmation_date else None
            })
        
        return {
            "bookings": booking_list,
            "total": total,
            "page": page,
            "size": len(booking_list),
            "pages": pages
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_user_bookings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user bookings"
        )


@router.post("/{booking_reference}/cancel")
def cancel_booking(
    booking_reference: str,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a booking."""
    try:
        booking_service = get_booking_service()
        
        result = booking_service.cancel_booking(
            db=db,
            booking_reference=booking_reference,
            user_id=current_user.id,
            reason=reason
        )
        
        return result
        
    except BookingServiceError as e:
        logger.error(f"Booking service error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error in cancel_booking: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel booking"
        )


@router.post("/ticket/validate")
def validate_ticket(
    validation_request: TicketValidationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate a ticket for event entry."""
    try:
        booking_service = get_booking_service()
        
        result = booking_service.validate_ticket(
            db=db,
            ticket_number=validation_request.ticket_number,
            validation_location=validation_request.validation_location
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Unexpected error in validate_ticket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to validate ticket"
        )


@router.get("/ticket/{ticket_number}")
def get_ticket_details(
    ticket_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get ticket details."""
    try:
        from ..models.booking import Ticket
        from sqlalchemy.orm import joinedload
        
        ticket = db.query(Ticket).options(
            joinedload(Ticket.booking),
            joinedload(Ticket.ticket_type),
            joinedload(Ticket.booking).joinedload("event")
        ).filter(Ticket.ticket_number == ticket_number).first()
        
        if not ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Check if user owns this ticket
        if ticket.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        return {
            "ticket": {
                "ticket_number": ticket.ticket_number,
                "status": ticket.ticket_status.value,
                "holder_name": ticket.holder_name,
                "holder_email": ticket.holder_email,
                "qr_code": ticket.qr_code,
                "barcode": ticket.barcode,
                "issued_date": ticket.issued_date.isoformat(),
                "valid_from": ticket.valid_from.isoformat() if ticket.valid_from else None,
                "valid_until": ticket.valid_until.isoformat() if ticket.valid_until else None,
                "check_in_time": ticket.check_in_time.isoformat() if ticket.check_in_time else None,
                "check_in_location": ticket.check_in_location
            },
            "booking": {
                "booking_reference": ticket.booking.booking_reference,
                "status": ticket.booking.booking_status.value
            } if ticket.booking else None,
            "event": {
                "id": ticket.booking.event.id,
                "title": ticket.booking.event.title,
                "date": ticket.booking.event.date.isoformat() if ticket.booking.event.date else None,
                "location": ticket.booking.event.location
            } if ticket.booking and ticket.booking.event else None,
            "ticket_type": {
                "name": ticket.ticket_type.name,
                "description": ticket.ticket_type.description
            } if ticket.ticket_type else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_ticket_details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket details"
        )


@router.get("/event/{event_id}/ticket-types")
def get_event_ticket_types(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get available ticket types for an event."""
    try:
        from ..models.booking import TicketType
        from ..models.event import Event
        
        # Verify event exists
        event = db.query(Event).filter(Event.id == event_id).first()
        if not event:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Event not found"
            )
        
        # Get active ticket types
        ticket_types = db.query(TicketType).filter(
            TicketType.event_id == event_id,
            TicketType.is_active == True
        ).all()
        
        # Check availability and sale periods
        now = datetime.now()
        
        ticket_list = []
        for ticket_type in ticket_types:
            # Check if sales are active
            sale_active = True
            if ticket_type.sale_start and now < ticket_type.sale_start:
                sale_active = False
            if ticket_type.sale_end and now > ticket_type.sale_end:
                sale_active = False
            
            ticket_list.append({
                "id": ticket_type.id,
                "name": ticket_type.name,
                "description": ticket_type.description,
                "price": float(ticket_type.price),
                "currency": ticket_type.currency,
                "available_quantity": ticket_type.available_quantity,
                "total_quantity": ticket_type.total_quantity,
                "min_purchase": ticket_type.min_purchase,
                "max_purchase": ticket_type.max_purchase,
                "sale_start": ticket_type.sale_start.isoformat() if ticket_type.sale_start else None,
                "sale_end": ticket_type.sale_end.isoformat() if ticket_type.sale_end else None,
                "sale_active": sale_active,
                "sold_out": ticket_type.available_quantity <= 0,
                "external_provider": ticket_type.external_provider
            })
        
        return {
            "event_id": event_id,
            "event_title": event.title,
            "ticket_types": ticket_list
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_event_ticket_types: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket types"
        )


@router.get("/statistics/overview")
def get_booking_statistics(
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get booking statistics overview."""
    try:
        # Check if user has permission to view statistics (admin only)
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        booking_service = get_booking_service()
        stats = booking_service.get_booking_statistics(db=db, event_id=event_id)
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_booking_statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve booking statistics"
        )


@router.get("/admin/bookings")
def get_all_bookings(
    event_id: Optional[int] = Query(None, description="Filter by event ID"),
    status_filter: Optional[str] = Query(None, description="Filter by booking status"),
    customer_email: Optional[str] = Query(None, description="Filter by customer email"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(50, ge=1, le=200, description="Page size"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bookings (admin only)."""
    try:
        # Check admin permission
        if not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        
        from ..models.booking import Booking
        from sqlalchemy.orm import joinedload
        
        query = db.query(Booking).options(
            joinedload(Booking.event),
            joinedload(Booking.ticket_type),
            joinedload(Booking.user)
        )
        
        # Apply filters
        if event_id:
            query = query.filter(Booking.event_id == event_id)
        
        if status_filter:
            try:
                status_enum = BookingStatus(status_filter)
                query = query.filter(Booking.booking_status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )
        
        if customer_email:
            query = query.filter(Booking.customer_email.ilike(f"%{customer_email}%"))
        
        # Get total count and apply pagination
        total = query.count()
        skip = (page - 1) * size
        pages = (total + size - 1) // size if total > 0 else 0
        
        bookings = query.order_by(Booking.booking_date.desc()).offset(skip).limit(size).all()
        
        # Format response
        booking_list = []
        for booking in bookings:
            booking_list.append({
                "id": booking.id,
                "booking_reference": booking.booking_reference,
                "status": booking.booking_status.value,
                "customer_name": booking.customer_name,
                "customer_email": booking.customer_email,
                "customer_phone": booking.customer_phone,
                "event": {
                    "id": booking.event.id,
                    "title": booking.event.title,
                    "date": booking.event.date.isoformat() if booking.event.date else None
                } if booking.event else None,
                "ticket_type": {
                    "name": booking.ticket_type.name
                } if booking.ticket_type else None,
                "quantity": booking.quantity,
                "total_price": float(booking.total_price),
                "currency": booking.currency,
                "booking_date": booking.booking_date.isoformat(),
                "confirmation_date": booking.confirmation_date.isoformat() if booking.confirmation_date else None,
                "external_provider": booking.external_provider
            })
        
        return {
            "bookings": booking_list,
            "total": total,
            "page": page,
            "size": len(booking_list),
            "pages": pages,
            "filters": {
                "event_id": event_id,
                "status": status_filter,
                "customer_email": customer_email
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_all_bookings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve bookings"
        )