"""
Event booking and ticketing service with external API integration.
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from decimal import Decimal
import requests
import json

from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from .database import get_db
from .config import settings
from ..models.booking import (
    Booking, Payment, Ticket, TicketType, BookingHistory,
    ExternalProviderConfig, BookingStatus, PaymentStatus, TicketStatus,
    PaymentMethod
)
from ..models.event import Event
from ..models.user import User

logger = logging.getLogger(__name__)


class BookingServiceError(Exception):
    """Base exception for booking service errors."""
    pass


class ExternalProviderError(Exception):
    """Exception for external provider integration errors."""
    pass


class BookingService:
    """Service for managing event bookings and ticketing."""
    
    def __init__(self):
        self.supported_providers = ["entrio", "eventbrite", "ticketmaster", "internal"]
        self.default_booking_expiry_minutes = 15
        
        logger.info("Booking service initialized")
    
    def create_booking(
        self, 
        db: Session,
        user_id: int,
        event_id: int,
        ticket_type_id: int,
        quantity: int,
        customer_info: Dict[str, str],
        payment_method: PaymentMethod = PaymentMethod.CREDIT_CARD
    ) -> Dict[str, Any]:
        """Create a new booking with payment processing."""
        try:
            # Validate ticket availability with event relationship
            from sqlalchemy.orm import joinedload
            ticket_type = db.query(TicketType).options(
                joinedload(TicketType.event)
            ).filter(TicketType.id == ticket_type_id).first()
            if not ticket_type:
                raise BookingServiceError("Ticket type not found")
            
            if ticket_type.available_quantity < quantity:
                raise BookingServiceError("Insufficient ticket availability")
            
            # Validate quantity limits
            if quantity < ticket_type.min_purchase:
                raise BookingServiceError(f"Minimum purchase quantity is {ticket_type.min_purchase}")
            
            if quantity > ticket_type.max_purchase:
                raise BookingServiceError(f"Maximum purchase quantity is {ticket_type.max_purchase}")
            
            # Check sale period
            now = datetime.now()
            if ticket_type.sale_start and now < ticket_type.sale_start:
                raise BookingServiceError("Ticket sales have not started yet")
            
            if ticket_type.sale_end and now > ticket_type.sale_end:
                raise BookingServiceError("Ticket sales have ended")
            
            # Calculate pricing
            unit_price = ticket_type.price
            total_price = unit_price * quantity
            
            # Get commission rate for user-generated events
            commission_rate = Decimal('0.0')  # Default no commission
            if ticket_type.event.is_user_generated:
                commission_rate = ticket_type.event.platform_commission_rate / 100
            
            platform_commission = total_price * commission_rate
            organizer_revenue = total_price - platform_commission
            
            # Create booking
            booking = Booking(
                user_id=user_id,
                event_id=event_id,
                ticket_type_id=ticket_type_id,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                currency=ticket_type.currency,
                customer_name=customer_info.get("name", ""),
                customer_email=customer_info.get("email", ""),
                customer_phone=customer_info.get("phone", ""),
                platform_commission_rate=commission_rate * 100,  # Store as percentage
                platform_commission_amount=platform_commission,
                organizer_revenue=organizer_revenue,
                expiry_date=now + timedelta(minutes=self.default_booking_expiry_minutes)
            )
            
            db.add(booking)
            db.flush()  # Get booking ID
            
            # Reserve tickets
            ticket_type.available_quantity -= quantity
            db.add(ticket_type)
            
            # Create booking history
            history = BookingHistory(
                booking_id=booking.id,
                previous_status=None,
                new_status=BookingStatus.PENDING.value,
                change_reason="Booking created",
                changed_by=f"user_{user_id}"
            )
            db.add(history)
            
            # Process payment
            payment_result = self._process_payment(
                db, booking, payment_method, customer_info
            )
            
            if payment_result["status"] == "success":
                # Update booking status
                booking.booking_status = BookingStatus.PAID
                booking.confirmation_date = now
                
                # Generate tickets
                tickets = self._generate_tickets(db, booking)
                
                # External provider integration
                external_result = None
                if ticket_type.external_provider:
                    try:
                        external_result = self._sync_with_external_provider(
                            booking, "create_booking"
                        )
                    except ExternalProviderError as e:
                        logger.warning(f"External provider sync failed: {e}")
                
                db.commit()
                
                return {
                    "status": "success",
                    "booking": {
                        "id": booking.id,
                        "booking_reference": booking.booking_reference,
                        "status": booking.booking_status.value,
                        "total_price": float(booking.total_price),
                        "currency": booking.currency,
                        "confirmation_date": booking.confirmation_date.isoformat(),
                        "expiry_date": booking.expiry_date.isoformat() if booking.expiry_date else None
                    },
                    "payment": payment_result,
                    "tickets": [
                        {
                            "ticket_number": t.ticket_number,
                            "holder_name": t.holder_name,
                            "qr_code": t.qr_code
                        } for t in tickets
                    ],
                    "external_result": external_result
                }
            else:
                # Payment failed - release reserved tickets
                ticket_type.available_quantity += quantity
                booking.booking_status = BookingStatus.CANCELLED
                
                db.commit()
                
                return {
                    "status": "payment_failed",
                    "message": payment_result.get("error", "Payment processing failed"),
                    "booking_reference": booking.booking_reference
                }
                
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in create_booking: {e}")
            raise BookingServiceError("Database operation failed")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in create_booking: {e}")
            raise BookingServiceError(str(e))
    
    def _process_payment(
        self,
        db: Session,
        booking: Booking,
        payment_method: PaymentMethod,
        customer_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process payment for booking using Stripe."""
        try:
            # Create payment record
            payment = Payment(
                booking_id=booking.id,
                amount=booking.total_price,
                currency=booking.currency,
                payment_method=payment_method,
                payment_description=f"Event booking {booking.booking_reference}"
            )
            
            db.add(payment)
            db.flush()
            
            # Use Stripe for real payment processing
            if payment_method == PaymentMethod.CREDIT_CARD:
                result = self._process_stripe_payment(payment, booking, customer_info)
            elif payment_method == PaymentMethod.PAYPAL:
                # For now, use mock PayPal (can be replaced with real PayPal SDK later)
                result = self._process_paypal_payment(payment, customer_info)
            else:
                result = self._process_generic_payment(payment, customer_info)
            
            # Update payment record
            payment.payment_status = PaymentStatus.COMPLETED if result["success"] else PaymentStatus.FAILED
            payment.external_payment_id = result.get("payment_intent_id") or result.get("payment_id")
            payment.external_transaction_id = result.get("transaction_id")
            payment.payment_gateway_response = result.get("gateway_response", {})
            payment.processed_date = datetime.now()
            
            if not result["success"]:
                payment.failure_reason = result.get("error", "Payment failed")
            
            db.add(payment)
            
            return {
                "status": "success" if result["success"] else "failed",
                "payment_id": payment.payment_reference,
                "external_payment_id": result.get("payment_intent_id") or result.get("payment_id"),
                "client_secret": result.get("client_secret"),  # For frontend Stripe integration
                "error": result.get("error")
            }
            
        except Exception as e:
            logger.error(f"Payment processing error: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _process_stripe_payment(
        self, 
        payment: Payment, 
        booking: Booking, 
        customer_info: Dict[str, str]
    ) -> Dict[str, Any]:
        """Process payment via Stripe."""
        try:
            from .stripe_service import get_stripe_service
            
            stripe_service = get_stripe_service()
            
            # Create Stripe payment intent
            result = stripe_service.create_payment_intent(
                amount=payment.amount,
                currency=payment.currency.lower(),
                booking_reference=booking.booking_reference,
                customer_email=customer_info.get("email", ""),
                event_title=booking.event.title if booking.event else "Event Booking",
                organizer_id=getattr(booking.event, 'organizer_id', None) if booking.event else None,
                platform_commission=booking.platform_commission_amount
            )
            
            if result["success"]:
                logger.info(f"Stripe payment intent created for booking {booking.booking_reference}")
                return {
                    "success": True,
                    "payment_intent_id": result["payment_intent_id"],
                    "client_secret": result["client_secret"],
                    "transaction_id": result["payment_intent_id"],
                    "gateway_response": {
                        "status": result["status"],
                        "provider": "stripe",
                        "metadata": result.get("metadata", {})
                    }
                }
            else:
                logger.error(f"Stripe payment failed for booking {booking.booking_reference}: {result}")
                return {
                    "success": False,
                    "error": result.get("message", "Stripe payment failed"),
                    "gateway_response": {
                        "status": "failed",
                        "provider": "stripe",
                        "error_code": result.get("error"),
                        "decline_code": result.get("decline_code")
                    }
                }
                
        except Exception as e:
            logger.error(f"Stripe payment processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "gateway_response": {
                    "status": "error",
                    "provider": "stripe",
                    "error": str(e)
                }
            }
    
    def _process_credit_card_payment(self, payment: Payment, customer_info: Dict[str, str]) -> Dict[str, Any]:
        """Mock credit card payment processing."""
        # In production, integrate with Stripe, Square, or similar
        logger.info(f"Processing credit card payment {payment.payment_reference}")
        
        # Mock successful payment (90% success rate)
        import random
        success = random.random() > 0.1
        
        if success:
            return {
                "success": True,
                "payment_id": f"cc_{payment.payment_reference}",
                "transaction_id": f"txn_{payment.id}_{datetime.now().timestamp()}",
                "gateway_response": {
                    "status": "completed",
                    "authorization_code": f"AUTH{random.randint(100000, 999999)}",
                    "last_four": "1234"
                }
            }
        else:
            return {
                "success": False,
                "error": "Credit card declined",
                "gateway_response": {
                    "status": "declined",
                    "decline_code": "insufficient_funds"
                }
            }
    
    def _process_paypal_payment(self, payment: Payment, customer_info: Dict[str, str]) -> Dict[str, Any]:
        """Mock PayPal payment processing."""
        # In production, integrate with PayPal API
        logger.info(f"Processing PayPal payment {payment.payment_reference}")
        
        return {
            "success": True,
            "payment_id": f"pp_{payment.payment_reference}",
            "transaction_id": f"paypal_txn_{payment.id}",
            "gateway_response": {
                "status": "completed",
                "payer_email": customer_info.get("email", ""),
                "paypal_transaction_id": f"PP{payment.id}TX{datetime.now().timestamp()}"
            }
        }
    
    def _process_generic_payment(self, payment: Payment, customer_info: Dict[str, str]) -> Dict[str, Any]:
        """Mock generic payment processing."""
        logger.info(f"Processing generic payment {payment.payment_reference}")
        
        return {
            "success": True,
            "payment_id": f"gen_{payment.payment_reference}",
            "transaction_id": f"gen_txn_{payment.id}",
            "gateway_response": {
                "status": "completed",
                "method": payment.payment_method.value
            }
        }
    
    def _generate_tickets(self, db: Session, booking: Booking) -> List[Ticket]:
        """Generate individual tickets for booking."""
        tickets = []
        
        for i in range(booking.quantity):
            ticket = Ticket(
                booking_id=booking.id,
                ticket_type_id=booking.ticket_type_id,
                user_id=booking.user_id,
                holder_name=booking.customer_name,
                holder_email=booking.customer_email,
                valid_from=datetime.now(),
                valid_until=booking.event.date if booking.event.date else None
            )
            
            db.add(ticket)
            db.flush()  # Get ticket ID for QR code generation
            
            # Generate QR code
            ticket.generate_qr_code()
            tickets.append(ticket)
        
        return tickets
    
    def _sync_with_external_provider(self, booking: Booking, action: str) -> Dict[str, Any]:
        """Sync booking with external provider."""
        try:
            provider = booking.ticket_type.external_provider
            
            if provider == "entrio":
                return self._sync_with_entrio(booking, action)
            elif provider == "eventbrite":
                return self._sync_with_eventbrite(booking, action)
            else:
                logger.warning(f"Unsupported external provider: {provider}")
                return {"status": "not_supported", "provider": provider}
                
        except Exception as e:
            logger.error(f"External provider sync error: {e}")
            raise ExternalProviderError(str(e))
    
    def _sync_with_entrio(self, booking: Booking, action: str) -> Dict[str, Any]:
        """Sync with Entrio ticketing system."""
        # Mock Entrio API integration
        logger.info(f"Syncing booking {booking.booking_reference} with Entrio - {action}")
        
        # In production, implement actual Entrio API calls
        return {
            "status": "success",
            "provider": "entrio",
            "external_booking_id": f"entrio_{booking.id}",
            "sync_timestamp": datetime.now().isoformat()
        }
    
    def _sync_with_eventbrite(self, booking: Booking, action: str) -> Dict[str, Any]:
        """Sync with Eventbrite ticketing system."""
        # Mock Eventbrite API integration
        logger.info(f"Syncing booking {booking.booking_reference} with Eventbrite - {action}")
        
        # In production, implement actual Eventbrite API calls
        return {
            "status": "success",
            "provider": "eventbrite",
            "external_booking_id": f"eventbrite_{booking.id}",
            "sync_timestamp": datetime.now().isoformat()
        }
    
    def get_booking(self, db: Session, booking_reference: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        """Get booking details."""
        query = db.query(Booking).filter(Booking.booking_reference == booking_reference)
        
        if user_id:
            query = query.filter(Booking.user_id == user_id)
        
        booking = query.first()
        if not booking:
            raise BookingServiceError("Booking not found")
        
        # Get associated tickets
        tickets = db.query(Ticket).filter(Ticket.booking_id == booking.id).all()
        
        # Get payment history
        payments = db.query(Payment).filter(Payment.booking_id == booking.id).all()
        
        return {
            "booking": {
                "id": booking.id,
                "booking_reference": booking.booking_reference,
                "status": booking.booking_status.value,
                "event_id": booking.event_id,
                "event_title": booking.event.title if booking.event else None,
                "ticket_type": booking.ticket_type.name if booking.ticket_type else None,
                "quantity": booking.quantity,
                "unit_price": float(booking.unit_price),
                "total_price": float(booking.total_price),
                "currency": booking.currency,
                "customer_name": booking.customer_name,
                "customer_email": booking.customer_email,
                "booking_date": booking.booking_date.isoformat(),
                "confirmation_date": booking.confirmation_date.isoformat() if booking.confirmation_date else None,
                "expiry_date": booking.expiry_date.isoformat() if booking.expiry_date else None
            },
            "tickets": [
                {
                    "ticket_number": t.ticket_number,
                    "status": t.ticket_status.value,
                    "holder_name": t.holder_name,
                    "qr_code": t.qr_code,
                    "check_in_time": t.check_in_time.isoformat() if t.check_in_time else None
                } for t in tickets
            ],
            "payments": [
                {
                    "payment_reference": p.payment_reference,
                    "amount": float(p.amount),
                    "currency": p.currency,
                    "method": p.payment_method.value,
                    "status": p.payment_status.value,
                    "payment_date": p.payment_date.isoformat() if p.payment_date else None
                } for p in payments
            ]
        }
    
    def cancel_booking(self, db: Session, booking_reference: str, user_id: int, reason: str = None) -> Dict[str, Any]:
        """Cancel a booking and process refund if applicable."""
        try:
            booking = db.query(Booking).filter(
                Booking.booking_reference == booking_reference,
                Booking.user_id == user_id
            ).first()
            
            if not booking:
                raise BookingServiceError("Booking not found")
            
            if booking.booking_status == BookingStatus.CANCELLED:
                raise BookingServiceError("Booking is already cancelled")
            
            # Check cancellation policy
            event_date = booking.event.date
            now = datetime.now().date()
            
            if event_date and event_date < now:
                raise BookingServiceError("Cannot cancel booking for past events")
            
            # Process refund if payment was completed
            refund_result = None
            if booking.booking_status == BookingStatus.PAID:
                refund_result = self._process_refund(db, booking, reason)
            
            # Update booking status
            previous_status = booking.booking_status
            booking.booking_status = BookingStatus.CANCELLED
            
            # Cancel associated tickets
            tickets = db.query(Ticket).filter(Ticket.booking_id == booking.id).all()
            for ticket in tickets:
                ticket.ticket_status = TicketStatus.CANCELLED
            
            # Release ticket availability
            booking.ticket_type.available_quantity += booking.quantity
            
            # Create booking history
            history = BookingHistory(
                booking_id=booking.id,
                previous_status=previous_status.value,
                new_status=BookingStatus.CANCELLED.value,
                change_reason=reason or "Cancelled by customer",
                changed_by=f"user_{user_id}"
            )
            db.add(history)
            
            # External provider sync
            external_result = None
            if booking.ticket_type.external_provider:
                try:
                    external_result = self._sync_with_external_provider(booking, "cancel_booking")
                except ExternalProviderError as e:
                    logger.warning(f"External provider cancellation sync failed: {e}")
            
            db.commit()
            
            return {
                "status": "success",
                "booking_reference": booking.booking_reference,
                "cancellation_date": datetime.now().isoformat(),
                "refund_result": refund_result,
                "external_result": external_result
            }
            
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error in cancel_booking: {e}")
            raise BookingServiceError("Database operation failed")
        except Exception as e:
            db.rollback()
            logger.error(f"Error in cancel_booking: {e}")
            raise BookingServiceError(str(e))
    
    def _process_refund(self, db: Session, booking: Booking, reason: str = None) -> Dict[str, Any]:
        """Process refund for cancelled booking."""
        try:
            # Find the payment to refund
            payment = db.query(Payment).filter(
                Payment.booking_id == booking.id,
                Payment.payment_status == PaymentStatus.COMPLETED
            ).first()
            
            if not payment:
                return {"status": "no_payment_found"}
            
            # Calculate refund amount (could implement cancellation fees here)
            refund_amount = payment.amount
            
            # Process refund via payment gateway
            refund_result = self._process_payment_gateway_refund(payment, refund_amount, reason)
            
            if refund_result["success"]:
                # Update payment record
                payment.payment_status = PaymentStatus.REFUNDED
                payment.refund_amount = refund_amount
                payment.refund_reason = reason
                payment.refund_date = datetime.now()
                
                return {
                    "status": "success",
                    "refund_amount": float(refund_amount),
                    "currency": payment.currency,
                    "refund_reference": refund_result.get("refund_id"),
                    "processing_time": "3-5 business days"
                }
            else:
                return {
                    "status": "failed",
                    "error": refund_result.get("error", "Refund processing failed")
                }
                
        except Exception as e:
            logger.error(f"Refund processing error: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _process_payment_gateway_refund(self, payment: Payment, amount: Decimal, reason: str = None) -> Dict[str, Any]:
        """Process refund via payment gateway (Stripe or fallback)."""
        try:
            # Try Stripe refund if payment was processed via Stripe
            if payment.external_payment_id and payment.external_payment_id.startswith(('pi_', 'ch_')):
                return self._process_stripe_refund(payment, amount, reason)
            else:
                # Fallback to mock refund for other payment methods
                logger.info(f"Processing mock refund for payment {payment.payment_reference}")
                return {
                    "success": True,
                    "refund_id": f"refund_{payment.payment_reference}",
                    "gateway_response": {
                        "status": "processed",
                        "refund_amount": float(amount),
                        "estimated_arrival": "3-5 business days"
                    }
                }
        except Exception as e:
            logger.error(f"Refund processing error: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _process_stripe_refund(self, payment: Payment, amount: Decimal, reason: str = None) -> Dict[str, Any]:
        """Process refund via Stripe."""
        try:
            from .stripe_service import get_stripe_service
            
            stripe_service = get_stripe_service()
            
            # Create Stripe refund
            result = stripe_service.create_refund(
                payment_intent_id=payment.external_payment_id,
                amount=amount,
                reason=reason or "requested_by_customer"
            )
            
            if result["success"]:
                logger.info(f"Stripe refund created for payment {payment.payment_reference}")
                return {
                    "success": True,
                    "refund_id": result["refund_id"],
                    "gateway_response": {
                        "status": result["status"],
                        "provider": "stripe",
                        "refund_amount": result["amount"],
                        "currency": result["currency"],
                        "receipt_number": result.get("receipt_number")
                    }
                }
            else:
                logger.error(f"Stripe refund failed for payment {payment.payment_reference}: {result}")
                return {
                    "success": False,
                    "error": result.get("error", "Stripe refund failed"),
                    "gateway_response": {
                        "status": "failed",
                        "provider": "stripe"
                    }
                }
                
        except Exception as e:
            logger.error(f"Stripe refund processing error: {e}")
            return {
                "success": False,
                "error": str(e),
                "gateway_response": {
                    "status": "error",
                    "provider": "stripe",
                    "error": str(e)
                }
            }
    
    def validate_ticket(self, db: Session, ticket_number: str, validation_location: str = None) -> Dict[str, Any]:
        """Validate ticket for event entry."""
        ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
        
        if not ticket:
            return {"status": "invalid", "message": "Ticket not found"}
        
        if ticket.ticket_status != TicketStatus.ACTIVE:
            return {"status": "invalid", "message": f"Ticket status: {ticket.ticket_status.value}"}
        
        if ticket.check_in_time:
            return {"status": "already_used", "message": "Ticket already used", "check_in_time": ticket.check_in_time.isoformat()}
        
        # Check validity period
        now = datetime.now()
        if ticket.valid_until and now > ticket.valid_until:
            return {"status": "expired", "message": "Ticket has expired"}
        
        if ticket.valid_from and now < ticket.valid_from:
            return {"status": "not_yet_valid", "message": "Ticket is not yet valid"}
        
        # Mark ticket as used
        ticket.check_in_time = now
        ticket.check_in_location = validation_location
        ticket.ticket_status = TicketStatus.USED
        
        db.commit()
        
        return {
            "status": "valid",
            "message": "Ticket validated successfully",
            "ticket": {
                "ticket_number": ticket.ticket_number,
                "holder_name": ticket.holder_name,
                "event_title": ticket.booking.event.title if ticket.booking.event else None,
                "check_in_time": ticket.check_in_time.isoformat()
            }
        }
    
    def get_booking_statistics(self, db: Session, event_id: Optional[int] = None) -> Dict[str, Any]:
        """Get booking statistics."""
        query = db.query(Booking)
        
        if event_id:
            query = query.filter(Booking.event_id == event_id)
        
        # Get statistics
        total_bookings = query.count()
        confirmed_bookings = query.filter(Booking.booking_status == BookingStatus.CONFIRMED).count()
        paid_bookings = query.filter(Booking.booking_status == BookingStatus.PAID).count()
        cancelled_bookings = query.filter(Booking.booking_status == BookingStatus.CANCELLED).count()
        
        # Get revenue statistics
        revenue_query = query.filter(Booking.booking_status.in_([BookingStatus.CONFIRMED, BookingStatus.PAID]))
        total_revenue = db.execute(
            text("SELECT COALESCE(SUM(total_price), 0) FROM bookings WHERE booking_status IN ('confirmed', 'paid')")
        ).scalar() or 0
        
        return {
            "total_bookings": total_bookings,
            "confirmed_bookings": confirmed_bookings,
            "paid_bookings": paid_bookings,
            "cancelled_bookings": cancelled_bookings,
            "total_revenue": float(total_revenue),
            "cancellation_rate": (cancelled_bookings / total_bookings * 100) if total_bookings > 0 else 0,
            "payment_success_rate": (paid_bookings / total_bookings * 100) if total_bookings > 0 else 0
        }


# Global service instance
booking_service = BookingService()


def get_booking_service() -> BookingService:
    """Get booking service instance."""
    return booking_service