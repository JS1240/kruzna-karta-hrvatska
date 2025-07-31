"""add user events support

Revision ID: 011_add_user_events_support
Revises: 010_add_social_features
Create Date: 2025-01-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '011_add_user_events_support'
down_revision: Union[str, None] = '010_add_social_features'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add user-generated events support"""
    
    # Add new columns to events table
    op.add_column('events', sa.Column('organizer_id', sa.Integer(), nullable=True))
    op.add_column('events', sa.Column('approval_status', sa.String(20), server_default='pending', nullable=False))
    op.add_column('events', sa.Column('platform_commission_rate', sa.Numeric(5, 2), server_default='5.0', nullable=False))
    op.add_column('events', sa.Column('is_user_generated', sa.Boolean(), server_default='false', nullable=False))
    
    # Add foreign key constraint
    op.create_foreign_key('events_organizer_id_fkey', 'events', 'users', ['organizer_id'], ['id'])
    
    # Add indexes for better performance
    op.create_index('ix_events_organizer_id', 'events', ['organizer_id'])
    op.create_index('ix_events_approval_status', 'events', ['approval_status'])
    op.create_index('ix_events_is_user_generated', 'events', ['is_user_generated'])
    
    # Update existing check constraints
    op.drop_constraint('events_source_check', 'events')
    op.create_check_constraint('events_source_check', 'events', 
                              "source IN ('entrio', 'croatia', 'manual', 'api', 'facebook', 'eventbrite', 'user_generated')")
    
    # Add approval status check constraint
    op.create_check_constraint('events_approval_check', 'events', 
                              "approval_status IN ('pending', 'approved', 'rejected')")
    
    # Add event_organizer role if it doesn't exist
    op.execute("""
        INSERT INTO user_roles (name, description, permissions) 
        VALUES ('event_organizer', 'Can create and manage their own events', '["create_events", "manage_own_events"]')
        ON CONFLICT (name) DO NOTHING;
    """)


def downgrade() -> None:
    """Remove user-generated events support"""
    
    # Drop check constraints
    op.drop_constraint('events_approval_check', 'events')
    op.drop_constraint('events_source_check', 'events')
    
    # Recreate original source check constraint
    op.create_check_constraint('events_source_check', 'events', 
                              "source IN ('entrio', 'croatia', 'manual', 'api', 'facebook', 'eventbrite')")
    
    # Drop indexes
    op.drop_index('ix_events_is_user_generated', 'events')
    op.drop_index('ix_events_approval_status', 'events')
    op.drop_index('ix_events_organizer_id', 'events')
    
    # Drop foreign key constraint
    op.drop_constraint('events_organizer_id_fkey', 'events')
    
    # Drop columns
    op.drop_column('events', 'is_user_generated')
    op.drop_column('events', 'platform_commission_rate')
    op.drop_column('events', 'approval_status')
    op.drop_column('events', 'organizer_id')
    
    # Remove event_organizer role
    op.execute("DELETE FROM user_roles WHERE name = 'event_organizer';")