from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, Numeric, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB, INET
from ..core.database import Base


class EventView(Base):
    """Track individual event views for analytics."""
    __tablename__ = "event_views"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)  # Null for anonymous users
    
    # Session and tracking
    session_id = Column(String(255), nullable=True, index=True)  # Track anonymous sessions
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)
    referrer = Column(String(500), nullable=True)
    
    # Geographic data
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    latitude = Column(Numeric(10, 8), nullable=True)
    longitude = Column(Numeric(11, 8), nullable=True)
    
    # Context
    source = Column(String(50), nullable=True)  # 'search', 'category', 'featured', 'direct'
    language = Column(String(10), nullable=True)  # Language user was viewing in
    device_type = Column(String(20), nullable=True)  # 'mobile', 'tablet', 'desktop'
    
    # Engagement metrics
    view_duration = Column(Integer, nullable=True)  # Seconds spent on page
    is_bounce = Column(Boolean, default=True)  # Updated if user views other pages
    
    # Timestamps
    viewed_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    event = relationship("Event")
    user = relationship("User")


class SearchLog(Base):
    """Track search queries and results for analytics."""
    __tablename__ = "search_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Search details
    query = Column(String(500), nullable=False, index=True)
    filters = Column(JSONB, nullable=True)  # Store search filters as JSON
    results_count = Column(Integer, nullable=False)
    
    # User interaction
    clicked_event_id = Column(Integer, ForeignKey('events.id'), nullable=True)
    click_position = Column(Integer, nullable=True)  # Position in search results
    
    # Context
    language = Column(String(10), nullable=True)
    source = Column(String(50), nullable=True)  # 'main_search', 'category_filter', etc.
    
    # Timestamps
    searched_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    clicked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User")
    clicked_event = relationship("Event")


class UserInteraction(Base):
    """Track user interactions with events and platform features."""
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    session_id = Column(String(255), nullable=True, index=True)
    
    # Interaction details
    interaction_type = Column(String(50), nullable=False, index=True)  # 'favorite', 'share', 'click', 'scroll'
    entity_type = Column(String(50), nullable=False)  # 'event', 'category', 'venue'
    entity_id = Column(Integer, nullable=False)
    
    # Context and metadata
    context = Column(JSONB, nullable=True)  # Additional interaction data
    value = Column(String(255), nullable=True)  # Interaction value (e.g., share platform)
    
    # Timestamps
    interacted_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user = relationship("User")


class EventPerformanceMetrics(Base):
    """Aggregated performance metrics for events."""
    __tablename__ = "event_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey('events.id'), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)  # Metrics date (daily aggregation)
    
    # View metrics
    total_views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    anonymous_views = Column(Integer, default=0)
    authenticated_views = Column(Integer, default=0)
    
    # Engagement metrics
    avg_view_duration = Column(Numeric(10, 2), default=0)
    bounce_rate = Column(Numeric(5, 2), default=0)  # Percentage
    total_favorites = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)
    
    # Geographic distribution
    top_countries = Column(JSONB, nullable=True)  # Top 5 countries with view counts
    top_cities = Column(JSONB, nullable=True)  # Top 5 cities with view counts
    
    # Traffic sources
    search_views = Column(Integer, default=0)
    direct_views = Column(Integer, default=0)
    referral_views = Column(Integer, default=0)
    featured_views = Column(Integer, default=0)
    
    # Device breakdown
    mobile_views = Column(Integer, default=0)
    tablet_views = Column(Integer, default=0)
    desktop_views = Column(Integer, default=0)
    
    # Language distribution
    language_breakdown = Column(JSONB, nullable=True)  # Language code -> view count
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    event = relationship("Event")
    
    # Unique constraint for daily metrics
    __table_args__ = (
        Index('idx_event_metrics_daily', 'event_id', 'date'),
    )


class PlatformMetrics(Base):
    """Overall platform performance metrics."""
    __tablename__ = "platform_metrics"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # 'daily', 'weekly', 'monthly'
    
    # User metrics
    total_users = Column(Integer, default=0)
    new_users = Column(Integer, default=0)
    active_users = Column(Integer, default=0)
    returning_users = Column(Integer, default=0)
    
    # Content metrics
    total_events = Column(Integer, default=0)
    new_events = Column(Integer, default=0)
    featured_events = Column(Integer, default=0)
    events_by_category = Column(JSONB, nullable=True)
    
    # Engagement metrics
    total_page_views = Column(Integer, default=0)
    total_sessions = Column(Integer, default=0)
    avg_session_duration = Column(Numeric(10, 2), default=0)
    total_searches = Column(Integer, default=0)
    
    # Popular content
    top_events = Column(JSONB, nullable=True)  # Top 10 events by views
    top_categories = Column(JSONB, nullable=True)  # Top categories by engagement
    top_cities = Column(JSONB, nullable=True)  # Top cities by event views
    
    # Geographic insights
    user_countries = Column(JSONB, nullable=True)  # Country distribution
    event_geographic_distribution = Column(JSONB, nullable=True)
    
    # Performance indicators
    bounce_rate = Column(Numeric(5, 2), default=0)
    conversion_rate = Column(Numeric(5, 2), default=0)  # Views to favorites ratio
    search_success_rate = Column(Numeric(5, 2), default=0)  # Searches with clicks
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CategoryMetrics(Base):
    """Performance metrics for event categories."""
    __tablename__ = "category_metrics"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey('event_categories.id'), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Basic metrics
    total_events = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    
    # Engagement
    total_favorites = Column(Integer, default=0)
    total_shares = Column(Integer, default=0)
    avg_view_duration = Column(Numeric(10, 2), default=0)
    
    # Search performance
    search_appearances = Column(Integer, default=0)
    search_clicks = Column(Integer, default=0)
    search_ctr = Column(Numeric(5, 2), default=0)  # Click-through rate
    
    # Popular events in category
    top_events = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    category = relationship("EventCategory")


class VenueMetrics(Base):
    """Performance metrics for venues."""
    __tablename__ = "venue_metrics"

    id = Column(Integer, primary_key=True, index=True)
    venue_id = Column(Integer, ForeignKey('venues.id'), nullable=False, index=True)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Basic metrics
    total_events = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    unique_views = Column(Integer, default=0)
    
    # Engagement
    total_favorites = Column(Integer, default=0)
    venue_page_views = Column(Integer, default=0)  # Direct venue page views
    
    # Event performance at venue
    avg_event_views = Column(Numeric(10, 2), default=0)
    most_popular_event_types = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    venue = relationship("Venue")


class AlertThreshold(Base):
    """Define alert thresholds for metrics monitoring."""
    __tablename__ = "alert_thresholds"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, unique=True)
    threshold_type = Column(String(20), nullable=False)  # 'min', 'max', 'percentage_change'
    threshold_value = Column(Numeric(15, 2), nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Alert settings
    alert_frequency = Column(String(20), default='daily')  # 'daily', 'hourly', 'immediate'
    notification_channels = Column(JSONB, nullable=True)  # Email, Slack, etc.
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class MetricAlert(Base):
    """Store triggered metric alerts."""
    __tablename__ = "metric_alerts"

    id = Column(Integer, primary_key=True, index=True)
    threshold_id = Column(Integer, ForeignKey('alert_thresholds.id'), nullable=False)
    metric_name = Column(String(100), nullable=False, index=True)
    
    # Alert details
    current_value = Column(Numeric(15, 2), nullable=False)
    threshold_value = Column(Numeric(15, 2), nullable=False)
    alert_message = Column(Text, nullable=False)
    severity = Column(String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    
    # Status
    is_resolved = Column(Boolean, default=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    triggered_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    threshold = relationship("AlertThreshold")
    resolver = relationship("User")


# Database indexes for performance
Index('idx_event_views_event_date', EventView.event_id, EventView.viewed_at)
Index('idx_event_views_user_date', EventView.user_id, EventView.viewed_at)
Index('idx_search_logs_query', SearchLog.query)
Index('idx_search_logs_date', SearchLog.searched_at)
Index('idx_user_interactions_type_date', UserInteraction.interaction_type, UserInteraction.interacted_at)
Index('idx_performance_metrics_event_date', EventPerformanceMetrics.event_id, EventPerformanceMetrics.date)
Index('idx_platform_metrics_type_date', PlatformMetrics.metric_type, PlatformMetrics.date)
Index('idx_category_metrics_date', CategoryMetrics.category_id, CategoryMetrics.date)
Index('idx_venue_metrics_date', VenueMetrics.venue_id, VenueMetrics.date)
Index('idx_metric_alerts_triggered', MetricAlert.triggered_at, MetricAlert.is_resolved)