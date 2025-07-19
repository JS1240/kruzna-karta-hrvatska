"""Add venue_coordinates table for geocoding cache

Revision ID: 013_add_venue_coordinates_table
Revises: 012_add_commission_tracking
Create Date: 2024-07-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '013_add_venue_coordinates_table'
down_revision: Union[str, None] = '012_add_commission_tracking'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add venue_coordinates table for geocoding cache."""
    op.create_table(
        'venue_coordinates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('venue_name', sa.String(500), nullable=False),
        sa.Column('latitude', sa.Numeric(10, 8), nullable=False),
        sa.Column('longitude', sa.Numeric(11, 8), nullable=False),
        sa.Column('accuracy', sa.String(50), nullable=True),
        sa.Column('confidence', sa.Numeric(3, 2), nullable=True),
        sa.Column('source', sa.String(50), nullable=True),
        sa.Column('place_name', sa.String(500), nullable=True),
        sa.Column('place_type', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.Index('idx_venue_coordinates_location', 'latitude', 'longitude'),
    )
    
    # Add a unique constraint to prevent duplicate venue names
    op.create_index('idx_venue_coordinates_name_unique', 'venue_coordinates', ['venue_name'], unique=True)


def downgrade() -> None:
    """Remove venue_coordinates table."""
    op.drop_table('venue_coordinates')