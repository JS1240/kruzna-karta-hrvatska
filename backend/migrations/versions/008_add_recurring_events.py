"""Add recurring events and event series

Revision ID: 008_add_recurring_events
Revises: 007_add_booking_system
Create Date: 2025-01-08 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_add_recurring_events'
down_revision = '007_add_booking_system'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create event_series table
    op.create_table('event_series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organizer_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('venue_id', sa.Integer(), nullable=True),
        sa.Column('series_status', sa.Enum('ACTIVE', 'PAUSED', 'COMPLETED', 'CANCELLED', name='seriesstatus'), nullable=True),
        sa.Column('is_template_based', sa.Boolean(), nullable=True),
        sa.Column('auto_publish', sa.Boolean(), nullable=True),
        sa.Column('advance_notice_days', sa.Integer(), nullable=True),
        sa.Column('template_title', sa.String(length=500), nullable=True),
        sa.Column('template_description', sa.Text(), nullable=True),
        sa.Column('template_price', sa.String(length=100), nullable=True),
        sa.Column('template_image', sa.String(length=1000), nullable=True),
        sa.Column('template_tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('template_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.String(length=50), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('recurrence_pattern', sa.Enum('DAILY', 'WEEKLY', 'BIWEEKLY', 'MONTHLY', 'YEARLY', 'CUSTOM', name='recurrencepattern'), nullable=False),
        sa.Column('recurrence_interval', sa.Integer(), nullable=True),
        sa.Column('recurrence_end_type', sa.Enum('NEVER', 'AFTER_OCCURRENCES', 'ON_DATE', name='recurrenceendtype'), nullable=True),
        sa.Column('recurrence_end_date', sa.Date(), nullable=True),
        sa.Column('max_occurrences', sa.Integer(), nullable=True),
        sa.Column('custom_recurrence_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('excluded_dates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('included_dates', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recurrence_days', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_instances', sa.Integer(), nullable=True),
        sa.Column('published_instances', sa.Integer(), nullable=True),
        sa.Column('completed_instances', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('last_generated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['event_categories.id'], ),
        sa.ForeignKeyConstraint(['organizer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['venue_id'], ['venues.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_series_id'), 'event_series', ['id'], unique=False)
    op.create_index(op.f('ix_event_series_title'), 'event_series', ['title'], unique=False)
    
    # Create event_instances table
    op.create_table('event_instances',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.String(length=100), nullable=True),
        sa.Column('image', sa.String(length=1000), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=True),
        sa.Column('scheduled_date', sa.Date(), nullable=False),
        sa.Column('scheduled_time', sa.String(length=50), nullable=True),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('title_overridden', sa.Boolean(), nullable=True),
        sa.Column('description_overridden', sa.Boolean(), nullable=True),
        sa.Column('price_overridden', sa.Boolean(), nullable=True),
        sa.Column('image_overridden', sa.Boolean(), nullable=True),
        sa.Column('location_overridden', sa.Boolean(), nullable=True),
        sa.Column('time_overridden', sa.Boolean(), nullable=True),
        sa.Column('instance_status', sa.Enum('SCHEDULED', 'PUBLISHED', 'CANCELLED', 'COMPLETED', 'MODIFIED', name='eventinstancestatus'), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=False),
        sa.Column('is_exception', sa.Boolean(), nullable=True),
        sa.Column('event_id', sa.Integer(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('instance_notes', sa.Text(), nullable=True),
        sa.Column('custom_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['series_id'], ['event_series.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id')
    )
    op.create_index(op.f('ix_event_instances_id'), 'event_instances', ['id'], unique=False)
    op.create_index(op.f('ix_event_instances_scheduled_date'), 'event_instances', ['scheduled_date'], unique=False)
    op.create_index(op.f('ix_event_instances_title'), 'event_instances', ['title'], unique=False)
    
    # Create series_modifications table
    op.create_table('series_modifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=False),
        sa.Column('modification_type', sa.String(length=50), nullable=False),
        sa.Column('field_changed', sa.String(length=100), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('applies_to_future', sa.Boolean(), nullable=True),
        sa.Column('applies_to_existing', sa.Boolean(), nullable=True),
        sa.Column('affected_instance_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('modified_by', sa.Integer(), nullable=True),
        sa.Column('modification_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('applied_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['modified_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['series_id'], ['event_series.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create instance_modifications table
    op.create_table('instance_modifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instance_id', sa.Integer(), nullable=False),
        sa.Column('modification_type', sa.String(length=50), nullable=False),
        sa.Column('field_changed', sa.String(length=100), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('modified_by', sa.Integer(), nullable=True),
        sa.Column('affects_future_instances', sa.Boolean(), nullable=True),
        sa.Column('modification_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['instance_id'], ['event_instances.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['modified_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create recurrence_rules table
    op.create_table('recurrence_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=False),
        sa.Column('frequency', sa.String(length=20), nullable=False),
        sa.Column('interval', sa.Integer(), nullable=True),
        sa.Column('count', sa.Integer(), nullable=True),
        sa.Column('until_date', sa.Date(), nullable=True),
        sa.Column('by_weekday', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('by_monthday', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('by_month', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('by_setpos', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('week_start', sa.Integer(), nullable=True),
        sa.Column('by_yearday', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('by_weekno', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('rule_name', sa.String(length=100), nullable=True),
        sa.Column('rule_description', sa.Text(), nullable=True),
        sa.Column('custom_logic', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['series_id'], ['event_series.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create series_templates table
    op.create_table('series_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('default_recurrence_pattern', sa.Enum('DAILY', 'WEEKLY', 'BIWEEKLY', 'MONTHLY', 'YEARLY', 'CUSTOM', name='recurrencepattern'), nullable=True),
        sa.Column('default_recurrence_interval', sa.Integer(), nullable=True),
        sa.Column('default_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('template_title_pattern', sa.String(length=500), nullable=True),
        sa.Column('template_description', sa.Text(), nullable=True),
        sa.Column('template_tags', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('template_metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('suggested_advance_notice_days', sa.Integer(), nullable=True),
        sa.Column('suggested_auto_publish', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_system_template', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create event_instance_view table (materialized view)
    op.create_table('event_instance_view',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('series_id', sa.Integer(), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=True),
        sa.Column('scheduled_date', sa.Date(), nullable=True),
        sa.Column('scheduled_time', sa.String(length=50), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('series_title', sa.String(length=500), nullable=True),
        sa.Column('organizer_name', sa.String(length=255), nullable=True),
        sa.Column('category_name', sa.String(length=255), nullable=True),
        sa.Column('venue_name', sa.String(length=255), nullable=True),
        sa.Column('has_tickets', sa.Boolean(), nullable=True),
        sa.Column('tickets_available', sa.Integer(), nullable=True),
        sa.Column('search_text', sa.Text(), nullable=True),
        sa.Column('last_updated', sa.DateTime(), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_event_instance_view_scheduled_date'), 'event_instance_view', ['scheduled_date'], unique=False)
    op.create_index(op.f('ix_event_instance_view_series_id'), 'event_instance_view', ['series_id'], unique=False)
    op.create_index(op.f('ix_event_instance_view_status'), 'event_instance_view', ['status'], unique=False)
    op.create_index(op.f('ix_event_instance_view_title'), 'event_instance_view', ['title'], unique=False)
    
    # Set default values
    op.execute("ALTER TABLE event_series ALTER COLUMN series_status SET DEFAULT 'ACTIVE'")
    op.execute("ALTER TABLE event_series ALTER COLUMN is_template_based SET DEFAULT true")
    op.execute("ALTER TABLE event_series ALTER COLUMN auto_publish SET DEFAULT false")
    op.execute("ALTER TABLE event_series ALTER COLUMN advance_notice_days SET DEFAULT 30")
    op.execute("ALTER TABLE event_series ALTER COLUMN timezone SET DEFAULT 'Europe/Zagreb'")
    op.execute("ALTER TABLE event_series ALTER COLUMN recurrence_interval SET DEFAULT 1")
    op.execute("ALTER TABLE event_series ALTER COLUMN recurrence_end_type SET DEFAULT 'NEVER'")
    op.execute("ALTER TABLE event_series ALTER COLUMN total_instances SET DEFAULT 0")
    op.execute("ALTER TABLE event_series ALTER COLUMN published_instances SET DEFAULT 0")
    op.execute("ALTER TABLE event_series ALTER COLUMN completed_instances SET DEFAULT 0")
    
    op.execute("ALTER TABLE event_instances ALTER COLUMN title_overridden SET DEFAULT false")
    op.execute("ALTER TABLE event_instances ALTER COLUMN description_overridden SET DEFAULT false")
    op.execute("ALTER TABLE event_instances ALTER COLUMN price_overridden SET DEFAULT false")
    op.execute("ALTER TABLE event_instances ALTER COLUMN image_overridden SET DEFAULT false")
    op.execute("ALTER TABLE event_instances ALTER COLUMN location_overridden SET DEFAULT false")
    op.execute("ALTER TABLE event_instances ALTER COLUMN time_overridden SET DEFAULT false")
    op.execute("ALTER TABLE event_instances ALTER COLUMN instance_status SET DEFAULT 'SCHEDULED'")
    op.execute("ALTER TABLE event_instances ALTER COLUMN is_exception SET DEFAULT false")
    
    op.execute("ALTER TABLE series_modifications ALTER COLUMN applies_to_future SET DEFAULT true")
    op.execute("ALTER TABLE series_modifications ALTER COLUMN applies_to_existing SET DEFAULT false")
    
    op.execute("ALTER TABLE instance_modifications ALTER COLUMN affects_future_instances SET DEFAULT false")
    
    op.execute("ALTER TABLE recurrence_rules ALTER COLUMN interval SET DEFAULT 1")
    op.execute("ALTER TABLE recurrence_rules ALTER COLUMN week_start SET DEFAULT 0")
    op.execute("ALTER TABLE recurrence_rules ALTER COLUMN timezone SET DEFAULT 'Europe/Zagreb'")
    
    op.execute("ALTER TABLE series_templates ALTER COLUMN default_recurrence_interval SET DEFAULT 1")
    op.execute("ALTER TABLE series_templates ALTER COLUMN suggested_advance_notice_days SET DEFAULT 30")
    op.execute("ALTER TABLE series_templates ALTER COLUMN suggested_auto_publish SET DEFAULT false")
    op.execute("ALTER TABLE series_templates ALTER COLUMN usage_count SET DEFAULT 0")
    op.execute("ALTER TABLE series_templates ALTER COLUMN is_public SET DEFAULT true")
    op.execute("ALTER TABLE series_templates ALTER COLUMN is_system_template SET DEFAULT false")
    
    op.execute("ALTER TABLE event_instance_view ALTER COLUMN has_tickets SET DEFAULT false")


def downgrade() -> None:
    # Drop tables in reverse order (due to foreign key constraints)
    op.drop_index(op.f('ix_event_instance_view_title'), table_name='event_instance_view')
    op.drop_index(op.f('ix_event_instance_view_status'), table_name='event_instance_view')
    op.drop_index(op.f('ix_event_instance_view_series_id'), table_name='event_instance_view')
    op.drop_index(op.f('ix_event_instance_view_scheduled_date'), table_name='event_instance_view')
    op.drop_table('event_instance_view')
    op.drop_table('series_templates')
    op.drop_table('recurrence_rules')
    op.drop_table('instance_modifications')
    op.drop_table('series_modifications')
    op.drop_index(op.f('ix_event_instances_title'), table_name='event_instances')
    op.drop_index(op.f('ix_event_instances_scheduled_date'), table_name='event_instances')
    op.drop_index(op.f('ix_event_instances_id'), table_name='event_instances')
    op.drop_table('event_instances')
    op.drop_index(op.f('ix_event_series_title'), table_name='event_series')
    op.drop_index(op.f('ix_event_series_id'), table_name='event_series')
    op.drop_table('event_series')
    
    # Drop custom enums
    op.execute('DROP TYPE IF EXISTS eventinstancestatus')
    op.execute('DROP TYPE IF EXISTS recurrenceendtype')
    op.execute('DROP TYPE IF EXISTS recurrencepattern')
    op.execute('DROP TYPE IF EXISTS seriesstatus')