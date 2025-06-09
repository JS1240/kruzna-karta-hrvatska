"""
Stripe webhook endpoints for handling payment events.
"""

from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from ..core.database import get_db
from ..core.stripe_service import get_stripe_service
from ..models.booking import Booking, Payment, BookingStatus, PaymentStatus

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stripe", tags=["stripe-webhooks"])


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events."""
    try:
        # Get raw payload and signature
        payload = await request.body()
        signature = request.headers.get("stripe-signature")
        
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing Stripe signature"
            )
        
        # Process webhook using Stripe service
        stripe_service = get_stripe_service()
        result = stripe_service.handle_webhook(payload, signature)
        
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Webhook processing failed")
            )
        
        # Handle specific event types
        if result.get("event_type") == "payment_succeeded":
            await handle_payment_success(
                db, 
                result["booking_reference"], 
                result["payment_intent_id"]
            )
        elif result.get("event_type") == "payment_failed":
            await handle_payment_failure(
                db, 
                result["booking_reference"], 
                result["payment_intent_id"]
            )
        elif result.get("event_type") == "dispute_created":
            await handle_dispute_created(
                db, 
                result["charge_id"], 
                result["dispute_id"]
            )
        
        return {"status": "success", "message": "Webhook processed"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


async def handle_payment_success(
    db: Session, 
    booking_reference: str, 
    payment_intent_id: str
):
    """Handle successful payment webhook."""
    try:
        # Find the booking
        booking = db.query(Booking).filter(
            Booking.booking_reference == booking_reference
        ).first()
        
        if not booking:
            logger.error(f"Booking not found for reference: {booking_reference}")
            return
        
        # Update booking status
        if booking.booking_status != BookingStatus.PAID:
            booking.booking_status = BookingStatus.PAID
            booking.confirmation_date = datetime.utcnow()
            
            # Update payment status
            payment = db.query(Payment).filter(
                Payment.booking_id == booking.id,
                Payment.external_payment_id == payment_intent_id
            ).first()
            
            if payment:
                payment.payment_status = PaymentStatus.COMPLETED
                payment.processed_date = datetime.utcnow()
            
            # Generate tickets if not already generated
            from ..core.booking import get_booking_service
            booking_service = get_booking_service()
            
            # Check if tickets already exist
            from ..models.booking import Ticket
            existing_tickets = db.query(Ticket).filter(
                Ticket.booking_id == booking.id
            ).count()
            
            if existing_tickets == 0:
                tickets = booking_service._generate_tickets(db, booking)
                logger.info(f"Generated {len(tickets)} tickets for booking {booking_reference}")
            
            db.commit()
            
            logger.info(f"Payment confirmed for booking {booking_reference}")
            
            # TODO: Send confirmation email to customer
            # TODO: Send notification to event organizer
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error handling payment success: {e}")


async def handle_payment_failure(
    db: Session, 
    booking_reference: str, 
    payment_intent_id: str
):
    """Handle failed payment webhook."""
    try:
        # Find the booking
        booking = db.query(Booking).filter(
            Booking.booking_reference == booking_reference
        ).first()
        
        if not booking:
            logger.error(f"Booking not found for reference: {booking_reference}")
            return
        
        # Update booking status
        if booking.booking_status not in [BookingStatus.CANCELLED, BookingStatus.EXPIRED]:
            booking.booking_status = BookingStatus.CANCELLED
            
            # Update payment status
            payment = db.query(Payment).filter(
                Payment.booking_id == booking.id,
                Payment.external_payment_id == payment_intent_id
            ).first()
            
            if payment:
                payment.payment_status = PaymentStatus.FAILED
                payment.failure_reason = "Payment failed via webhook"
            
            # Release ticket availability
            if booking.ticket_type:
                booking.ticket_type.available_quantity += booking.quantity
            
            db.commit()
            
            logger.info(f"Payment failed for booking {booking_reference}")
            
            # TODO: Send failure notification to customer
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error handling payment failure: {e}")


async def handle_dispute_created(
    db: Session, 
    charge_id: str, 
    dispute_id: str
):
    """Handle chargeback/dispute webhook."""
    try:
        # Find payment by charge ID
        payment = db.query(Payment).filter(
            Payment.external_payment_id == charge_id
        ).first()
        
        if payment:
            # Add dispute information to payment metadata
            if not payment.payment_gateway_response:
                payment.payment_gateway_response = {}
            
            payment.payment_gateway_response["dispute"] = {
                "dispute_id": dispute_id,
                "created_at": datetime.utcnow().isoformat(),
                "status": "created"
            }
            
            db.commit()
            
            logger.warning(f"Dispute created for charge {charge_id}: {dispute_id}")
            
            # TODO: Send notification to admin/finance team
            # TODO: Handle dispute response process
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error handling dispute creation: {e}")


@router.get("/config")
def get_stripe_config():
    """Get Stripe configuration for frontend."""
    from ..core.config import settings
    
    return {
        "publishable_key": settings.stripe_publishable_key,
        "currency": settings.currency.lower(),
        "supported_payment_methods": settings.payment_methods,
        "platform_commission_rate": settings.platform_commission_rate
    }