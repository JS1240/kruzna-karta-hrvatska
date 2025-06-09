"""Add booking and ticketing system

Revision ID: 007_add_booking_system
Revises: 006_add_analytics_tables
Create Date: 2025-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_add_booking_system'
down_revision = '006_add_analytics_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create ticket_types table
    op.create_table('ticket_types',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('total_quantity', sa.Integer(), nullable=False),
        sa.Column('available_quantity', sa.Integer(), nullable=False),
        sa.Column('min_purchase', sa.Integer(), nullable=True),
        sa.Column('max_purchase', sa.Integer(), nullable=True),
        sa.Column('sale_start', sa.DateTime(), nullable=True),
        sa.Column('sale_end', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('external_provider', sa.String(length=100), nullable=True),
        sa.Column('external_ticket_id', sa.String(length=255), nullable=True),
        sa.Column('external_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ticket_types_id'), 'ticket_types', ['id'], unique=False)
    
    # Create bookings table
    op.create_table('bookings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_reference', sa.String(length=100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('ticket_type_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('total_price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('booking_status', sa.Enum('PENDING', 'CONFIRMED', 'PAID', 'CANCELLED', 'REFUNDED', 'EXPIRED', name='bookingstatus'), nullable=True),
        sa.Column('customer_name', sa.String(length=255), nullable=False),
        sa.Column('customer_email', sa.String(length=255), nullable=False),
        sa.Column('customer_phone', sa.String(length=50), nullable=True),
        sa.Column('external_provider', sa.String(length=100), nullable=True),
        sa.Column('external_booking_id', sa.String(length=255), nullable=True),
        sa.Column('external_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('booking_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('confirmation_date', sa.DateTime(), nullable=True),
        sa.Column('expiry_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['ticket_type_id'], ['ticket_types.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_reference')
    )
    op.create_index(op.f('ix_bookings_booking_reference'), 'bookings', ['booking_reference'], unique=False)
    op.create_index(op.f('ix_bookings_id'), 'bookings', ['id'], unique=False)
    
    # Create payments table
    op.create_table('payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('payment_reference', sa.String(length=100), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False),
        sa.Column('payment_method', sa.Enum('CREDIT_CARD', 'BANK_TRANSFER', 'PAYPAL', 'APPLE_PAY', 'GOOGLE_PAY', 'CRYPTO', name='paymentmethod'), nullable=False),
        sa.Column('payment_status', sa.Enum('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'REFUNDED', 'PARTIALLY_REFUNDED', name='paymentstatus'), nullable=True),
        sa.Column('payment_provider', sa.String(length=100), nullable=True),
        sa.Column('external_payment_id', sa.String(length=255), nullable=True),
        sa.Column('external_transaction_id', sa.String(length=255), nullable=True),
        sa.Column('payment_gateway_response', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('payment_description', sa.Text(), nullable=True),
        sa.Column('failure_reason', sa.Text(), nullable=True),
        sa.Column('refund_amount', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('refund_reason', sa.Text(), nullable=True),
        sa.Column('payment_date', sa.DateTime(), nullable=True),
        sa.Column('processed_date', sa.DateTime(), nullable=True),
        sa.Column('refund_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_reference')
    )
    op.create_index(op.f('ix_payments_id'), 'payments', ['id'], unique=False)
    op.create_index(op.f('ix_payments_payment_reference'), 'payments', ['payment_reference'], unique=False)
    
    # Create tickets table
    op.create_table('tickets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticket_number', sa.String(length=100), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('ticket_type_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('ticket_status', sa.Enum('ACTIVE', 'USED', 'CANCELLED', 'EXPIRED', name='ticketstatus'), nullable=True),
        sa.Column('qr_code', sa.Text(), nullable=True),
        sa.Column('barcode', sa.String(length=255), nullable=True),
        sa.Column('holder_name', sa.String(length=255), nullable=True),
        sa.Column('holder_email', sa.String(length=255), nullable=True),
        sa.Column('check_in_time', sa.DateTime(), nullable=True),
        sa.Column('check_in_location', sa.String(length=255), nullable=True),
        sa.Column('validated_by', sa.String(length=255), nullable=True),
        sa.Column('external_provider', sa.String(length=100), nullable=True),
        sa.Column('external_ticket_id', sa.String(length=255), nullable=True),
        sa.Column('external_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('issued_date', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('valid_from', sa.DateTime(), nullable=True),
        sa.Column('valid_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['ticket_type_id'], ['ticket_types.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('ticket_number')
    )
    op.create_index(op.f('ix_tickets_id'), 'tickets', ['id'], unique=False)
    op.create_index(op.f('ix_tickets_ticket_number'), 'tickets', ['ticket_number'], unique=False)
    
    # Create booking_history table
    op.create_table('booking_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('previous_status', sa.String(length=50), nullable=True),
        sa.Column('new_status', sa.String(length=50), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('changed_by', sa.String(length=255), nullable=True),
        sa.Column('change_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create external_provider_configs table
    op.create_table('external_provider_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('provider_name', sa.String(length=100), nullable=False),
        sa.Column('api_endpoint', sa.String(length=500), nullable=True),
        sa.Column('api_key', sa.String(length=500), nullable=True),
        sa.Column('secret_key', sa.String(length=500), nullable=True),
        sa.Column('webhook_url', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('supported_features', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('rate_limits', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('provider_config', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_name')
    )
    
    # Set default values
    op.execute("ALTER TABLE ticket_types ALTER COLUMN min_purchase SET DEFAULT 1")
    op.execute("ALTER TABLE ticket_types ALTER COLUMN max_purchase SET DEFAULT 10")
    op.execute("ALTER TABLE ticket_types ALTER COLUMN is_active SET DEFAULT true")
    op.execute("ALTER TABLE ticket_types ALTER COLUMN currency SET DEFAULT 'EUR'")
    
    op.execute("ALTER TABLE bookings ALTER COLUMN currency SET DEFAULT 'EUR'")
    op.execute("ALTER TABLE bookings ALTER COLUMN booking_status SET DEFAULT 'PENDING'")
    
    op.execute("ALTER TABLE payments ALTER COLUMN currency SET DEFAULT 'EUR'")
    op.execute("ALTER TABLE payments ALTER COLUMN payment_status SET DEFAULT 'PENDING'")
    op.execute("ALTER TABLE payments ALTER COLUMN refund_amount SET DEFAULT 0")
    
    op.execute("ALTER TABLE tickets ALTER COLUMN ticket_status SET DEFAULT 'ACTIVE'")
    
    op.execute("ALTER TABLE external_provider_configs ALTER COLUMN is_active SET DEFAULT true")


def downgrade() -> None:
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_table('external_provider_configs')
    op.drop_table('booking_history')
    op.drop_index(op.f('ix_tickets_ticket_number'), table_name='tickets')
    op.drop_index(op.f('ix_tickets_id'), table_name='tickets')
    op.drop_table('tickets')
    op.drop_index(op.f('ix_payments_payment_reference'), table_name='payments')
    op.drop_index(op.f('ix_payments_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_bookings_id'), table_name='bookings')
    op.drop_index(op.f('ix_bookings_booking_reference'), table_name='bookings')
    op.drop_table('bookings')
    op.drop_index(op.f('ix_ticket_types_id'), table_name='ticket_types')
    op.drop_table('ticket_types')
    
    # Drop custom enums
    op.execute('DROP TYPE IF EXISTS ticketstatus')
    op.execute('DROP TYPE IF EXISTS paymentstatus')
    op.execute('DROP TYPE IF EXISTS paymentmethod')
    op.execute('DROP TYPE IF EXISTS bookingstatus')