"""
Stripe payment processing service for event bookings.
"""

import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Optional

import stripe

from .config import settings

logger = logging.getLogger(__name__)


class StripePaymentError(Exception):
    """Custom exception for Stripe payment errors."""

    pass


class StripeService:
    """Service for handling Stripe payment processing."""

    def __init__(self):
        """Initialize Stripe service with API keys."""
        # Set Stripe API key from settings
        stripe.api_key = getattr(settings, "stripe_secret_key", "sk_test_...")
        self.webhook_secret = getattr(settings, "stripe_webhook_secret", "")
        self.platform_fee_percentage = 5.0  # 5% platform fee

        logger.info("Stripe service initialized")

    def create_payment_intent(
        self,
        amount: Decimal,
        currency: str = "eur",
        booking_reference: str = "",
        customer_email: str = "",
        event_title: str = "",
        organizer_id: Optional[int] = None,
        platform_commission: Decimal = Decimal("0.0"),
    ) -> Dict[str, Any]:
        """
        Create a Stripe Payment Intent for event booking.

        Args:
            amount: Total amount in the smallest currency unit (cents for EUR)
            currency: Currency code (default: eur)
            booking_reference: Unique booking reference
            customer_email: Customer's email address
            event_title: Title of the event being booked
            organizer_id: ID of the event organizer (for future Connect integration)
            platform_commission: Platform commission amount

        Returns:
            Dict containing payment intent details
        """
        try:
            # Convert amount to cents (Stripe requires smallest currency unit)
            amount_cents = int(amount * 100)

            # Metadata for tracking
            metadata = {
                "booking_reference": booking_reference,
                "event_title": event_title[:500],  # Stripe has metadata value limits
                "organizer_id": str(organizer_id) if organizer_id else "",
                "platform_commission": str(platform_commission),
                "source": "kruzna_karta_user_events",
            }

            # Create payment intent
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                receipt_email=customer_email,
                description=f"Event Booking: {event_title}",
                metadata=metadata,
                automatic_payment_methods={
                    "enabled": True,
                },
                # Add application fee for platform commission (requires Stripe Connect)
                # application_fee_amount=int(platform_commission * 100) if organizer_id else None
            )

            logger.info(
                f"Created payment intent {payment_intent.id} for booking {booking_reference}"
            )

            return {
                "success": True,
                "payment_intent_id": payment_intent.id,
                "client_secret": payment_intent.client_secret,
                "amount": amount,
                "currency": currency,
                "status": payment_intent.status,
                "metadata": metadata,
            }

        except stripe.error.CardError as e:
            # Card was declined
            logger.error(f"Card declined for booking {booking_reference}: {e}")
            return {
                "success": False,
                "error": "card_declined",
                "message": str(e.user_message),
                "decline_code": e.decline_code,
            }

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters
            logger.error(f"Invalid Stripe request for booking {booking_reference}: {e}")
            return {
                "success": False,
                "error": "invalid_request",
                "message": "Invalid payment request parameters",
            }

        except stripe.error.AuthenticationError as e:
            # Authentication failed
            logger.error(f"Stripe authentication error: {e}")
            return {
                "success": False,
                "error": "authentication_error",
                "message": "Payment service authentication failed",
            }

        except stripe.error.APIConnectionError as e:
            # Network communication failed
            logger.error(f"Stripe API connection error: {e}")
            return {
                "success": False,
                "error": "network_error",
                "message": "Payment service temporarily unavailable",
            }

        except stripe.error.StripeError as e:
            # Generic Stripe error
            logger.error(f"Generic Stripe error for booking {booking_reference}: {e}")
            return {
                "success": False,
                "error": "payment_error",
                "message": "Payment processing failed",
            }

        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error creating payment intent: {e}")
            return {
                "success": False,
                "error": "unexpected_error",
                "message": "An unexpected error occurred",
            }

    def confirm_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """
        Confirm a payment intent (usually done on frontend, but here for completeness).

        Args:
            payment_intent_id: The payment intent ID from Stripe

        Returns:
            Dict containing confirmation result
        """
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            return {
                "success": True,
                "payment_intent_id": payment_intent.id,
                "status": payment_intent.status,
                "amount_received": payment_intent.amount_received,
                "charges": [
                    {
                        "id": charge.id,
                        "amount": charge.amount,
                        "paid": charge.paid,
                        "receipt_url": charge.receipt_url,
                    }
                    for charge in payment_intent.charges.data
                ],
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error confirming payment {payment_intent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "payment_intent_id": payment_intent_id,
            }

    def create_refund(
        self,
        payment_intent_id: str,
        amount: Optional[Decimal] = None,
        reason: str = "requested_by_customer",
    ) -> Dict[str, Any]:
        """
        Create a refund for a successful payment.

        Args:
            payment_intent_id: The payment intent ID to refund
            amount: Amount to refund (if partial), None for full refund
            reason: Reason for refund

        Returns:
            Dict containing refund result
        """
        try:
            # Get the payment intent to find the charge
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)

            if not payment_intent.charges.data:
                return {
                    "success": False,
                    "error": "no_charge_found",
                    "message": "No charge found for this payment intent",
                }

            charge_id = payment_intent.charges.data[0].id

            # Create refund parameters
            refund_params = {
                "charge": charge_id,
                "reason": reason,
                "metadata": {
                    "original_payment_intent": payment_intent_id,
                    "refund_timestamp": datetime.now(timezone.utc).isoformat(),
                },
            }

            # Add amount if partial refund
            if amount:
                refund_params["amount"] = int(amount * 100)  # Convert to cents

            # Create the refund
            refund = stripe.Refund.create(**refund_params)

            logger.info(
                f"Created refund {refund.id} for payment intent {payment_intent_id}"
            )

            return {
                "success": True,
                "refund_id": refund.id,
                "amount": refund.amount / 100,  # Convert back to currency units
                "currency": refund.currency,
                "status": refund.status,
                "receipt_number": refund.receipt_number,
            }

        except stripe.error.StripeError as e:
            logger.error(f"Error creating refund for {payment_intent_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "payment_intent_id": payment_intent_id,
            }

    def handle_webhook(self, payload: bytes, signature: str) -> Dict[str, Any]:
        """
        Handle Stripe webhook events.

        Args:
            payload: Raw webhook payload
            signature: Stripe signature header

        Returns:
            Dict containing webhook processing result
        """
        try:
            # Verify webhook signature
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )

            logger.info(f"Received Stripe webhook: {event['type']}")

            # Handle different event types
            if event["type"] == "payment_intent.succeeded":
                payment_intent = event["data"]["object"]
                return self._handle_payment_success(payment_intent)

            elif event["type"] == "payment_intent.payment_failed":
                payment_intent = event["data"]["object"]
                return self._handle_payment_failure(payment_intent)

            elif event["type"] == "charge.dispute.created":
                dispute = event["data"]["object"]
                return self._handle_dispute_created(dispute)

            else:
                # Unhandled event type
                logger.info(f"Unhandled webhook event type: {event['type']}")
                return {
                    "success": True,
                    "message": f"Received {event['type']} event",
                    "handled": False,
                }

        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            return {"success": False, "error": "invalid_payload"}

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return {"success": False, "error": "invalid_signature"}

    def _handle_payment_success(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle successful payment webhook."""
        booking_reference = payment_intent.get("metadata", {}).get("booking_reference")

        logger.info(f"Payment succeeded for booking {booking_reference}")

        # Here you would update your booking status in the database
        # This would be called from a webhook endpoint

        return {
            "success": True,
            "event_type": "payment_succeeded",
            "booking_reference": booking_reference,
            "payment_intent_id": payment_intent["id"],
        }

    def _handle_payment_failure(self, payment_intent: Dict[str, Any]) -> Dict[str, Any]:
        """Handle failed payment webhook."""
        booking_reference = payment_intent.get("metadata", {}).get("booking_reference")

        logger.warning(f"Payment failed for booking {booking_reference}")

        return {
            "success": True,
            "event_type": "payment_failed",
            "booking_reference": booking_reference,
            "payment_intent_id": payment_intent["id"],
        }

    def _handle_dispute_created(self, dispute: Dict[str, Any]) -> Dict[str, Any]:
        """Handle chargeback/dispute webhook."""
        charge_id = dispute["charge"]

        logger.warning(f"Dispute created for charge {charge_id}")

        return {
            "success": True,
            "event_type": "dispute_created",
            "charge_id": charge_id,
            "dispute_id": dispute["id"],
        }

    def get_payment_methods(self, customer_id: str) -> Dict[str, Any]:
        """
        Get saved payment methods for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Dict containing payment methods
        """
        try:
            payment_methods = stripe.PaymentMethod.list(
                customer=customer_id, type="card"
            )

            return {
                "success": True,
                "payment_methods": [
                    {
                        "id": pm.id,
                        "card": {
                            "brand": pm.card.brand,
                            "last4": pm.card.last4,
                            "exp_month": pm.card.exp_month,
                            "exp_year": pm.card.exp_year,
                        },
                    }
                    for pm in payment_methods.data
                ],
            }

        except stripe.error.StripeError as e:
            logger.error(
                f"Error fetching payment methods for customer {customer_id}: {e}"
            )
            return {"success": False, "error": str(e)}


# Global service instance
stripe_service = StripeService()


def get_stripe_service() -> StripeService:
    """Get Stripe service instance."""
    return stripe_service
