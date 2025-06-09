"""add commission tracking to bookings

Revision ID: 012_add_commission_tracking
Revises: 011_add_user_events_support
Create Date: 2025-01-08 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '012_add_commission_tracking'
down_revision: Union[str, None] = '011_add_user_events_support'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add commission tracking fields to bookings table"""
    
    # Add commission tracking columns to bookings table
    op.add_column('bookings', sa.Column('platform_commission_rate', sa.Numeric(5, 2), server_default='0.0', nullable=False))
    op.add_column('bookings', sa.Column('platform_commission_amount', sa.Numeric(10, 2), server_default='0.0', nullable=False))
    op.add_column('bookings', sa.Column('organizer_revenue', sa.Numeric(10, 2), server_default='0.0', nullable=False))


def downgrade() -> None:
    """Remove commission tracking fields from bookings table"""
    
    # Drop commission tracking columns
    op.drop_column('bookings', 'organizer_revenue')
    op.drop_column('bookings', 'platform_commission_amount')
    op.drop_column('bookings', 'platform_commission_rate')