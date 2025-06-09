"""
Event booking and ticketing models.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Text, JSON, Enum as SQLEnum, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum
import uuid

from ..core.database import Base


class BookingStatus(Enum):
    """Booking status enumeration."""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    EXPIRED = "expired"


class PaymentStatus(Enum):
    """Payment status enumeration."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class TicketStatus(Enum):
    """Ticket status enumeration."""
    ACTIVE = "active"
    USED = "used"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PaymentMethod(Enum):
    """Payment method enumeration."""
    CREDIT_CARD = "credit_card"
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    CRYPTO = "crypto"


class TicketType(Base):
    """Ticket type model for different ticket categories."""
    __tablename__ = "ticket_types"
    
    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    price = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    total_quantity = Column(Integer, nullable=False)
    available_quantity = Column(Integer, nullable=False)
    min_purchase = Column(Integer, default=1)
    max_purchase = Column(Integer, default=10)
    sale_start = Column(DateTime)
    sale_end = Column(DateTime)
    is_active = Column(Boolean, default=True)
    
    # External integration
    external_provider = Column(String(100))  # e.g., "entrio", "eventbrite"
    external_ticket_id = Column(String(255))
    external_metadata = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    event = relationship("Event", back_populates="ticket_types")
    bookings = relationship("Booking", back_populates="ticket_type")
    tickets = relationship("Ticket", back_populates="ticket_type")


class Booking(Base):
    """Booking model for event reservations."""
    __tablename__ = "bookings"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_reference = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_id = Column(Integer, ForeignKey("events.id"), nullable=False)
    ticket_type_id = Column(Integer, ForeignKey("ticket_types.id"), nullable=False)
    
    # Booking details
    quantity = Column(Integer, nullable=False)
    unit_price = Column(DECIMAL(10, 2), nullable=False)
    total_price = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    booking_status = Column(SQLEnum(BookingStatus), default=BookingStatus.PENDING)
    
    # Customer information
    customer_name = Column(String(255), nullable=False)
    customer_email = Column(String(255), nullable=False)
    customer_phone = Column(String(50))
    
    # Commission tracking for user-generated events
    platform_commission_rate = Column(DECIMAL(5, 2), default=0.0)  # Percentage
    platform_commission_amount = Column(DECIMAL(10, 2), default=0.0)  # Amount in currency
    organizer_revenue = Column(DECIMAL(10, 2), default=0.0)  # Amount after commission
    
    # External integration
    external_provider = Column(String(100))
    external_booking_id = Column(String(255))
    external_metadata = Column(JSON)
    
    # Timestamps
    booking_date = Column(DateTime, default=func.now())
    confirmation_date = Column(DateTime)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="bookings")
    event = relationship("Event", back_populates="bookings")
    ticket_type = relationship("TicketType", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking")
    tickets = relationship("Ticket", back_populates="booking")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.booking_reference:
            self.booking_reference = self._generate_booking_reference()
    
    def _generate_booking_reference(self):
        """Generate unique booking reference."""
        import secrets
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = secrets.token_hex(4).upper()
        return f"KK{timestamp}{random_part}"


class Payment(Base):
    """Payment model for booking transactions."""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    payment_reference = Column(String(100), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    
    # Payment details
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="EUR")
    payment_method = Column(SQLEnum(PaymentMethod), nullable=False)
    payment_status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    
    # External payment integration
    payment_provider = Column(String(100))  # e.g., "stripe", "paypal", "square"
    external_payment_id = Column(String(255))
    external_transaction_id = Column(String(255))
    payment_gateway_response = Column(JSON)
    
    # Payment metadata
    payment_description = Column(Text)
    failure_reason = Column(Text)
    refund_amount = Column(DECIMAL(10, 2), default=0)
    refund_reason = Column(Text)
    
    # Timestamps
    payment_date = Column(DateTime)
    processed_date = Column(DateTime)
    refund_date = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    booking = relationship("Booking", back_populates="payments")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.payment_reference:
            self.payment_reference = self._generate_payment_reference()
    
    def _generate_payment_reference(self):
        """Generate unique payment reference."""
        import secrets
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = secrets.token_hex(4).upper()
        return f"PAY{timestamp}{random_part}"


class Ticket(Base):
    """Individual ticket model."""
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(100), unique=True, nullable=False, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    ticket_type_id = Column(Integer, ForeignKey("ticket_types.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Ticket details
    ticket_status = Column(SQLEnum(TicketStatus), default=TicketStatus.ACTIVE)
    qr_code = Column(Text)  # QR code for ticket validation
    barcode = Column(String(255))  # Barcode for ticket scanning
    
    # Ticket holder information
    holder_name = Column(String(255))
    holder_email = Column(String(255))
    
    # Validation
    check_in_time = Column(DateTime)
    check_in_location = Column(String(255))
    validated_by = Column(String(255))
    
    # External integration
    external_provider = Column(String(100))
    external_ticket_id = Column(String(255))
    external_metadata = Column(JSON)
    
    # Timestamps
    issued_date = Column(DateTime, default=func.now())
    valid_from = Column(DateTime)
    valid_until = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    booking = relationship("Booking", back_populates="tickets")
    ticket_type = relationship("TicketType", back_populates="tickets")
    user = relationship("User", back_populates="tickets")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.ticket_number:
            self.ticket_number = self._generate_ticket_number()
    
    def _generate_ticket_number(self):
        """Generate unique ticket number."""
        import secrets
        timestamp = datetime.now().strftime("%Y%m%d")
        random_part = secrets.token_hex(6).upper()
        return f"TKT{timestamp}{random_part}"
    
    def generate_qr_code(self):
        """Generate QR code for ticket validation."""
        import qrcode
        import io
        import base64
        
        # Create QR code data
        qr_data = {
            "ticket_number": self.ticket_number,
            "booking_reference": self.booking.booking_reference,
            "event_id": self.booking.event_id,
            "holder_name": self.holder_name,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None
        }
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(qr_data))
        qr.make(fit=True)
        
        # Create QR code image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 string
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        self.qr_code = f"data:image/png;base64,{img_str}"
        return self.qr_code


class BookingHistory(Base):
    """Booking history model for audit trail."""
    __tablename__ = "booking_history"
    
    id = Column(Integer, primary_key=True, index=True)
    booking_id = Column(Integer, ForeignKey("bookings.id", ondelete="CASCADE"), nullable=False)
    
    # Status change information
    previous_status = Column(String(50))
    new_status = Column(String(50))
    change_reason = Column(Text)
    changed_by = Column(String(255))  # User or system that made the change
    
    # Additional metadata
    change_metadata = Column(JSON)
    
    # Timestamps
    changed_at = Column(DateTime, default=func.now())
    
    # Relationships
    booking = relationship("Booking")


class ExternalProviderConfig(Base):
    """Configuration for external booking providers."""
    __tablename__ = "external_provider_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(100), unique=True, nullable=False)
    
    # Provider details
    api_endpoint = Column(String(500))
    api_key = Column(String(500))
    secret_key = Column(String(500))
    webhook_url = Column(String(500))
    
    # Configuration
    is_active = Column(Boolean, default=True)
    supported_features = Column(JSON)  # List of supported features
    rate_limits = Column(JSON)  # API rate limiting configuration
    
    # Provider-specific settings
    provider_config = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())