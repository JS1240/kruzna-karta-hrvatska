"""Initial migration with enhanced event schema

Revision ID: 20250606_232105
Revises: 
Create Date: 2025-06-06T23:21:05.571598

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250606_232105'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create event_categories table
    op.create_table('event_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=7), nullable=True, default='#3B82F6'),
        sa.Column('icon', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('slug')
    )
    
    # Create venues table
    op.create_table('venues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), nullable=True, default='Croatia'),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=True),
        sa.Column('venue_type', sa.String(length=50), nullable=True),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name', 'city', name='_venue_name_city_uc')
    )
    
    # Create events table with enhanced schema
    op.create_table('events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('time', sa.String(length=50), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('price', sa.String(length=100), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('link', sa.String(length=1000), nullable=True),
        sa.Column('image', sa.String(length=1000), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('venue_id', sa.Integer(), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=False, default='manual'),
        sa.Column('external_id', sa.String(length=255), nullable=True),
        sa.Column('event_status', sa.String(length=20), nullable=True, default='active'),
        sa.Column('is_featured', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_recurring', sa.Boolean(), nullable=True, default=False),
        sa.Column('organizer', sa.String(length=255), nullable=True),
        sa.Column('age_restriction', sa.String(length=50), nullable=True),
        sa.Column('ticket_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.Text()), nullable=True),
        sa.Column('slug', sa.String(length=600), nullable=True),
        sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('end_time', sa.String(length=50), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True, default='Europe/Zagreb'),
        sa.Column('view_count', sa.Integer(), nullable=True, default=0),
        sa.Column('last_scraped_at', sa.DateTime(), nullable=True),
        sa.Column('scrape_hash', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['event_categories.id'], ),
        sa.ForeignKeyConstraint(['venue_id'], ['venues.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
        sa.CheckConstraint('date >= CURRENT_DATE - INTERVAL '1 year'', name='events_date_check'),
        sa.CheckConstraint('end_date IS NULL OR end_date >= date', name='events_end_date_check'),
        sa.CheckConstraint('event_status IN ('active', 'cancelled', 'postponed', 'sold_out', 'draft')', name='events_status_check'),
        sa.CheckConstraint('source IN ('entrio', 'croatia', 'manual', 'api', 'facebook', 'eventbrite')', name='events_source_check')
    )
    
    # Create indexes
    op.create_index('idx_events_date', 'events', ['date'])
    op.create_index('idx_events_location', 'events', ['location'])
    op.create_index('idx_events_name', 'events', ['name'])
    op.create_index('idx_events_category', 'events', ['category_id'])
    op.create_index('idx_events_venue', 'events', ['venue_id'])
    op.create_index('idx_events_source', 'events', ['source'])
    op.create_index('idx_events_status', 'events', ['event_status'])
    op.create_index('idx_events_featured', 'events', ['is_featured'], postgresql_where=sa.text('is_featured = true'))
    op.create_index('idx_events_date_status', 'events', ['date', 'event_status'])
    op.create_index('idx_events_tags', 'events', ['tags'], postgresql_using='gin')
    op.create_index('idx_events_coordinates', 'events', ['latitude', 'longitude'], postgresql_where=sa.text('latitude IS NOT NULL AND longitude IS NOT NULL'))
    op.create_index('idx_events_scrape_hash', 'events', ['scrape_hash'], postgresql_where=sa.text('scrape_hash IS NOT NULL'))
    op.create_index('idx_events_external_id', 'events', ['source', 'external_id'], postgresql_where=sa.text('external_id IS NOT NULL'))
    op.create_index('idx_venues_city', 'venues', ['city'])
    op.create_index('idx_venues_coordinates', 'venues', ['latitude', 'longitude'], postgresql_where=sa.text('latitude IS NOT NULL AND longitude IS NOT NULL'))
    op.create_index('idx_venues_name', 'venues', ['name'])
    op.create_index('idx_categories_slug', 'event_categories', ['slug'])
    
    # Create GIN indexes for full-text search
    op.execute('CREATE INDEX IF NOT EXISTS idx_events_location_gin ON events USING gin(to_tsvector('simple', location))')
    op.execute('CREATE INDEX IF NOT EXISTS idx_events_search ON events USING gin(search_vector)')


def downgrade() -> None:
    # Drop all indexes
    op.drop_index('idx_events_search', 'events')
    op.drop_index('idx_events_location_gin', 'events')
    op.drop_index('idx_categories_slug', 'event_categories')
    op.drop_index('idx_venues_name', 'venues')
    op.drop_index('idx_venues_coordinates', 'venues')
    op.drop_index('idx_venues_city', 'venues')
    op.drop_index('idx_events_external_id', 'events')
    op.drop_index('idx_events_scrape_hash', 'events')
    op.drop_index('idx_events_coordinates', 'events')
    op.drop_index('idx_events_tags', 'events')
    op.drop_index('idx_events_date_status', 'events')
    op.drop_index('idx_events_featured', 'events')
    op.drop_index('idx_events_status', 'events')
    op.drop_index('idx_events_source', 'events')
    op.drop_index('idx_events_venue', 'events')
    op.drop_index('idx_events_category', 'events')
    op.drop_index('idx_events_name', 'events')
    op.drop_index('idx_events_location', 'events')
    op.drop_index('idx_events_date', 'events')
    
    # Drop tables
    op.drop_table('events')
    op.drop_table('venues')
    op.drop_table('event_categories')
