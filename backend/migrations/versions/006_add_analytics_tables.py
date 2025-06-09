"""Add analytics and metrics tracking tables

Revision ID: 006
Revises: 005
Create Date: 2025-01-07 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create event_views table
    op.create_table('event_views',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('referrer', sa.String(length=500), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('device_type', sa.String(length=20), nullable=True),
        sa.Column('view_duration', sa.Integer(), nullable=True),
        sa.Column('is_bounce', sa.Boolean(), default=True),
        sa.Column('viewed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_event_views_event_date', 'event_views', ['event_id', 'viewed_at'])
    op.create_index('idx_event_views_user_date', 'event_views', ['user_id', 'viewed_at'])
    op.create_index(op.f('ix_event_views_event_id'), 'event_views', ['event_id'])
    op.create_index(op.f('ix_event_views_id'), 'event_views', ['id'])
    op.create_index(op.f('ix_event_views_session_id'), 'event_views', ['session_id'])
    op.create_index(op.f('ix_event_views_user_id'), 'event_views', ['user_id'])
    op.create_index(op.f('ix_event_views_viewed_at'), 'event_views', ['viewed_at'])

    # Create search_logs table
    op.create_table('search_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('query', sa.String(length=500), nullable=False),
        sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('results_count', sa.Integer(), nullable=False),
        sa.Column('clicked_event_id', sa.Integer(), nullable=True),
        sa.Column('click_position', sa.Integer(), nullable=True),
        sa.Column('language', sa.String(length=10), nullable=True),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('searched_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('clicked_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['clicked_event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_search_logs_date', 'search_logs', ['searched_at'])
    op.create_index('idx_search_logs_query', 'search_logs', ['query'])
    op.create_index(op.f('ix_search_logs_id'), 'search_logs', ['id'])
    op.create_index(op.f('ix_search_logs_query'), 'search_logs', ['query'])
    op.create_index(op.f('ix_search_logs_searched_at'), 'search_logs', ['searched_at'])
    op.create_index(op.f('ix_search_logs_session_id'), 'search_logs', ['session_id'])
    op.create_index(op.f('ix_search_logs_user_id'), 'search_logs', ['user_id'])

    # Create user_interactions table
    op.create_table('user_interactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('session_id', sa.String(length=255), nullable=True),
        sa.Column('interaction_type', sa.String(length=50), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('value', sa.String(length=255), nullable=True),
        sa.Column('interacted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_interactions_type_date', 'user_interactions', ['interaction_type', 'interacted_at'])
    op.create_index(op.f('ix_user_interactions_id'), 'user_interactions', ['id'])
    op.create_index(op.f('ix_user_interactions_interacted_at'), 'user_interactions', ['interacted_at'])
    op.create_index(op.f('ix_user_interactions_interaction_type'), 'user_interactions', ['interaction_type'])
    op.create_index(op.f('ix_user_interactions_session_id'), 'user_interactions', ['session_id'])
    op.create_index(op.f('ix_user_interactions_user_id'), 'user_interactions', ['user_id'])

    # Create event_performance_metrics table
    op.create_table('event_performance_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_views', sa.Integer(), default=0),
        sa.Column('unique_views', sa.Integer(), default=0),
        sa.Column('anonymous_views', sa.Integer(), default=0),
        sa.Column('authenticated_views', sa.Integer(), default=0),
        sa.Column('avg_view_duration', sa.Numeric(precision=10, scale=2), default=0),
        sa.Column('bounce_rate', sa.Numeric(precision=5, scale=2), default=0),
        sa.Column('total_favorites', sa.Integer(), default=0),
        sa.Column('total_shares', sa.Integer(), default=0),
        sa.Column('top_countries', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('top_cities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('search_views', sa.Integer(), default=0),
        sa.Column('direct_views', sa.Integer(), default=0),
        sa.Column('referral_views', sa.Integer(), default=0),
        sa.Column('featured_views', sa.Integer(), default=0),
        sa.Column('mobile_views', sa.Integer(), default=0),
        sa.Column('tablet_views', sa.Integer(), default=0),
        sa.Column('desktop_views', sa.Integer(), default=0),
        sa.Column('language_breakdown', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_event_metrics_daily', 'event_performance_metrics', ['event_id', 'date'])
    op.create_index('idx_performance_metrics_event_date', 'event_performance_metrics', ['event_id', 'date'])
    op.create_index(op.f('ix_event_performance_metrics_date'), 'event_performance_metrics', ['date'])
    op.create_index(op.f('ix_event_performance_metrics_event_id'), 'event_performance_metrics', ['event_id'])
    op.create_index(op.f('ix_event_performance_metrics_id'), 'event_performance_metrics', ['id'])

    # Create platform_metrics table
    op.create_table('platform_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('total_users', sa.Integer(), default=0),
        sa.Column('new_users', sa.Integer(), default=0),
        sa.Column('active_users', sa.Integer(), default=0),
        sa.Column('returning_users', sa.Integer(), default=0),
        sa.Column('total_events', sa.Integer(), default=0),
        sa.Column('new_events', sa.Integer(), default=0),
        sa.Column('featured_events', sa.Integer(), default=0),
        sa.Column('events_by_category', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('total_page_views', sa.Integer(), default=0),
        sa.Column('total_sessions', sa.Integer(), default=0),
        sa.Column('avg_session_duration', sa.Numeric(precision=10, scale=2), default=0),
        sa.Column('total_searches', sa.Integer(), default=0),
        sa.Column('top_events', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('top_categories', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('top_cities', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('user_countries', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('event_geographic_distribution', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('bounce_rate', sa.Numeric(precision=5, scale=2), default=0),
        sa.Column('conversion_rate', sa.Numeric(precision=5, scale=2), default=0),
        sa.Column('search_success_rate', sa.Numeric(precision=5, scale=2), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_platform_metrics_type_date', 'platform_metrics', ['metric_type', 'date'])
    op.create_index(op.f('ix_platform_metrics_date'), 'platform_metrics', ['date'])
    op.create_index(op.f('ix_platform_metrics_id'), 'platform_metrics', ['id'])
    op.create_index(op.f('ix_platform_metrics_metric_type'), 'platform_metrics', ['metric_type'])

    # Create category_metrics table
    op.create_table('category_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_events', sa.Integer(), default=0),
        sa.Column('total_views', sa.Integer(), default=0),
        sa.Column('unique_views', sa.Integer(), default=0),
        sa.Column('total_favorites', sa.Integer(), default=0),
        sa.Column('total_shares', sa.Integer(), default=0),
        sa.Column('avg_view_duration', sa.Numeric(precision=10, scale=2), default=0),
        sa.Column('search_appearances', sa.Integer(), default=0),
        sa.Column('search_clicks', sa.Integer(), default=0),
        sa.Column('search_ctr', sa.Numeric(precision=5, scale=2), default=0),
        sa.Column('top_events', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['event_categories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_category_metrics_date', 'category_metrics', ['category_id', 'date'])
    op.create_index(op.f('ix_category_metrics_category_id'), 'category_metrics', ['category_id'])
    op.create_index(op.f('ix_category_metrics_date'), 'category_metrics', ['date'])
    op.create_index(op.f('ix_category_metrics_id'), 'category_metrics', ['id'])

    # Create venue_metrics table
    op.create_table('venue_metrics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('venue_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('total_events', sa.Integer(), default=0),
        sa.Column('total_views', sa.Integer(), default=0),
        sa.Column('unique_views', sa.Integer(), default=0),
        sa.Column('total_favorites', sa.Integer(), default=0),
        sa.Column('venue_page_views', sa.Integer(), default=0),
        sa.Column('avg_event_views', sa.Numeric(precision=10, scale=2), default=0),
        sa.Column('most_popular_event_types', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['venue_id'], ['venues.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_venue_metrics_date', 'venue_metrics', ['venue_id', 'date'])
    op.create_index(op.f('ix_venue_metrics_date'), 'venue_metrics', ['date'])
    op.create_index(op.f('ix_venue_metrics_id'), 'venue_metrics', ['id'])
    op.create_index(op.f('ix_venue_metrics_venue_id'), 'venue_metrics', ['venue_id'])

    # Create alert_thresholds table
    op.create_table('alert_thresholds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('threshold_type', sa.String(length=20), nullable=False),
        sa.Column('threshold_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('alert_frequency', sa.String(length=20), default='daily'),
        sa.Column('notification_channels', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_name')
    )
    op.create_index(op.f('ix_alert_thresholds_id'), 'alert_thresholds', ['id'])

    # Create metric_alerts table
    op.create_table('metric_alerts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('threshold_id', sa.Integer(), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('current_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('threshold_value', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('alert_message', sa.Text(), nullable=False),
        sa.Column('severity', sa.String(length=20), default='medium'),
        sa.Column('is_resolved', sa.Boolean(), default=False),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('resolved_by', sa.Integer(), nullable=True),
        sa.Column('triggered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['threshold_id'], ['alert_thresholds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_metric_alerts_triggered', 'metric_alerts', ['triggered_at', 'is_resolved'])
    op.create_index(op.f('ix_metric_alerts_id'), 'metric_alerts', ['id'])
    op.create_index(op.f('ix_metric_alerts_metric_name'), 'metric_alerts', ['metric_name'])
    op.create_index(op.f('ix_metric_alerts_triggered_at'), 'metric_alerts', ['triggered_at'])


def downgrade() -> None:
    # Drop tables in reverse order due to foreign key constraints
    op.drop_table('metric_alerts')
    op.drop_table('alert_thresholds')
    op.drop_table('venue_metrics')
    op.drop_table('category_metrics')
    op.drop_table('platform_metrics')
    op.drop_table('event_performance_metrics')
    op.drop_table('user_interactions')
    op.drop_table('search_logs')
    op.drop_table('event_views')