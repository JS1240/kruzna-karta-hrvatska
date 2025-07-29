from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import Depends
from sqlalchemy import and_, case, desc, func, or_, text
from sqlalchemy.orm import Session

import pandas as pd
from sklearn.cluster import DBSCAN, KMeans
from sklearn.preprocessing import StandardScaler

from ..core.database import get_db
from ..models.analytics import (
    AlertThreshold,
    CategoryMetrics,
    EventPerformanceMetrics,
    EventView,
    MetricAlert,
    PlatformMetrics,
    SearchLog,
    UserInteraction,
    VenueMetrics,
)
from ..models.category import EventCategory
from ..models.event import Event
from ..models.user import User
from ..models.venue import Venue


class AnalyticsService:
    """Service for managing analytics tracking and metrics aggregation."""

    def __init__(self, db: Session):
        self.db = db

    # Event View Tracking
    def track_event_view(
        self,
        event_id: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        referrer: Optional[str] = None,
        country: Optional[str] = None,
        city: Optional[str] = None,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        source: Optional[str] = None,
        language: Optional[str] = None,
        device_type: Optional[str] = None,
    ) -> EventView:
        """Track an event view with comprehensive metadata."""

        view = EventView(
            event_id=event_id,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            city=city,
            latitude=latitude,
            longitude=longitude,
            source=source,
            language=language,
            device_type=device_type,
        )

        self.db.add(view)
        self.db.commit()
        self.db.refresh(view)
        return view

    def update_view_engagement(
        self, view_id: int, view_duration: int, is_bounce: bool = False
    ):
        """Update view engagement metrics."""

        view = self.db.query(EventView).filter(EventView.id == view_id).first()
        if view:
            view.view_duration = view_duration
            view.is_bounce = is_bounce
            self.db.commit()

    # Search Tracking
    def track_search(
        self,
        query: str,
        results_count: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        filters: Optional[Dict] = None,
        language: Optional[str] = None,
        source: Optional[str] = None,
    ) -> SearchLog:
        """Track a search query."""

        search_log = SearchLog(
            query=query,
            results_count=results_count,
            user_id=user_id,
            session_id=session_id,
            filters=filters,
            language=language,
            source=source,
        )

        self.db.add(search_log)
        self.db.commit()
        self.db.refresh(search_log)
        return search_log

    def track_search_click(
        self, search_log_id: int, clicked_event_id: int, click_position: int
    ):
        """Track when a user clicks on a search result."""

        search_log = (
            self.db.query(SearchLog).filter(SearchLog.id == search_log_id).first()
        )
        if search_log:
            search_log.clicked_event_id = clicked_event_id
            search_log.click_position = click_position
            search_log.clicked_at = func.now()
            self.db.commit()

    # User Interaction Tracking
    def track_user_interaction(
        self,
        interaction_type: str,
        entity_type: str,
        entity_id: int,
        user_id: Optional[int] = None,
        session_id: Optional[str] = None,
        context: Optional[Dict] = None,
        value: Optional[str] = None,
    ) -> UserInteraction:
        """Track user interactions with platform features."""

        interaction = UserInteraction(
            user_id=user_id,
            session_id=session_id,
            interaction_type=interaction_type,
            entity_type=entity_type,
            entity_id=entity_id,
            context=context,
            value=value,
        )

        self.db.add(interaction)
        self.db.commit()
        self.db.refresh(interaction)
        return interaction

    # Metrics Aggregation
    def aggregate_event_metrics(self, target_date: date) -> None:
        """Aggregate daily metrics for all events."""

        # Get all events that had views on the target date
        events_with_views = (
            self.db.query(EventView.event_id)
            .filter(func.date(EventView.viewed_at) == target_date)
            .distinct()
            .all()
        )

        for (event_id,) in events_with_views:
            self._aggregate_single_event_metrics(event_id, target_date)

    def _aggregate_single_event_metrics(self, event_id: int, target_date: date) -> None:
        """Aggregate metrics for a single event on a specific date."""

        # Check if metrics already exist for this date
        existing = (
            self.db.query(EventPerformanceMetrics)
            .filter(
                and_(
                    EventPerformanceMetrics.event_id == event_id,
                    func.date(EventPerformanceMetrics.date) == target_date,
                )
            )
            .first()
        )

        if existing:
            metrics = existing
        else:
            metrics = EventPerformanceMetrics(
                event_id=event_id,
                date=datetime.combine(target_date, datetime.min.time()),
            )
            self.db.add(metrics)

        # Get views for this event on this date
        views_query = self.db.query(EventView).filter(
            and_(
                EventView.event_id == event_id,
                func.date(EventView.viewed_at) == target_date,
            )
        )

        views = views_query.all()

        # Calculate metrics
        metrics.total_views = len(views)
        metrics.unique_views = len(set(v.user_id for v in views if v.user_id))
        metrics.anonymous_views = len([v for v in views if not v.user_id])
        metrics.authenticated_views = metrics.total_views - metrics.anonymous_views

        # Engagement metrics
        durations = [v.view_duration for v in views if v.view_duration]
        metrics.avg_view_duration = sum(durations) / len(durations) if durations else 0

        bounces = len([v for v in views if v.is_bounce])
        metrics.bounce_rate = (
            (bounces / metrics.total_views * 100) if metrics.total_views > 0 else 0
        )

        # Geographic distribution
        countries = {}
        cities = {}
        for view in views:
            if view.country:
                countries[view.country] = countries.get(view.country, 0) + 1
            if view.city:
                cities[view.city] = cities.get(view.city, 0) + 1

        metrics.top_countries = dict(
            sorted(countries.items(), key=lambda x: x[1], reverse=True)[:5]
        )
        metrics.top_cities = dict(
            sorted(cities.items(), key=lambda x: x[1], reverse=True)[:5]
        )

        # Traffic sources
        metrics.search_views = len([v for v in views if v.source == "search"])
        metrics.direct_views = len([v for v in views if v.source == "direct"])
        metrics.referral_views = len([v for v in views if v.source == "referral"])
        metrics.featured_views = len([v for v in views if v.source == "featured"])

        # Device breakdown
        metrics.mobile_views = len([v for v in views if v.device_type == "mobile"])
        metrics.tablet_views = len([v for v in views if v.device_type == "tablet"])
        metrics.desktop_views = len([v for v in views if v.device_type == "desktop"])

        # Language distribution
        languages = {}
        for view in views:
            if view.language:
                languages[view.language] = languages.get(view.language, 0) + 1
        metrics.language_breakdown = languages

        # Get favorites and shares for this event on this date
        favorites = (
            self.db.query(UserInteraction)
            .filter(
                and_(
                    UserInteraction.entity_type == "event",
                    UserInteraction.entity_id == event_id,
                    UserInteraction.interaction_type == "favorite",
                    func.date(UserInteraction.interacted_at) == target_date,
                )
            )
            .count()
        )

        shares = (
            self.db.query(UserInteraction)
            .filter(
                and_(
                    UserInteraction.entity_type == "event",
                    UserInteraction.entity_id == event_id,
                    UserInteraction.interaction_type == "share",
                    func.date(UserInteraction.interacted_at) == target_date,
                )
            )
            .count()
        )

        metrics.total_favorites = favorites
        metrics.total_shares = shares

        self.db.commit()

    def aggregate_platform_metrics(
        self, target_date: date, metric_type: str = "daily"
    ) -> None:
        """Aggregate platform-wide metrics."""

        # Check if metrics already exist
        existing = (
            self.db.query(PlatformMetrics)
            .filter(
                and_(
                    func.date(PlatformMetrics.date) == target_date,
                    PlatformMetrics.metric_type == metric_type,
                )
            )
            .first()
        )

        if existing:
            metrics = existing
        else:
            metrics = PlatformMetrics(
                date=datetime.combine(target_date, datetime.min.time()),
                metric_type=metric_type,
            )
            self.db.add(metrics)

        # User metrics
        metrics.total_users = self.db.query(User).count()
        metrics.new_users = (
            self.db.query(User)
            .filter(func.date(User.created_at) == target_date)
            .count()
        )

        # Active users (users who viewed events today)
        metrics.active_users = (
            self.db.query(EventView.user_id)
            .filter(
                and_(
                    EventView.user_id.isnot(None),
                    func.date(EventView.viewed_at) == target_date,
                )
            )
            .distinct()
            .count()
        )

        # Content metrics
        metrics.total_events = (
            self.db.query(Event).filter(Event.event_status == "active").count()
        )
        metrics.new_events = (
            self.db.query(Event)
            .filter(func.date(Event.created_at) == target_date)
            .count()
        )
        metrics.featured_events = (
            self.db.query(Event)
            .filter(and_(Event.is_featured == True, Event.event_status == "active"))
            .count()
        )

        # Engagement metrics
        metrics.total_page_views = (
            self.db.query(EventView)
            .filter(func.date(EventView.viewed_at) == target_date)
            .count()
        )

        metrics.total_searches = (
            self.db.query(SearchLog)
            .filter(func.date(SearchLog.searched_at) == target_date)
            .count()
        )

        # Performance indicators
        total_views = (
            self.db.query(EventView)
            .filter(func.date(EventView.viewed_at) == target_date)
            .count()
        )

        bounces = (
            self.db.query(EventView)
            .filter(
                and_(
                    func.date(EventView.viewed_at) == target_date,
                    EventView.is_bounce == True,
                )
            )
            .count()
        )

        metrics.bounce_rate = (bounces / total_views * 100) if total_views > 0 else 0

        # Search success rate
        successful_searches = (
            self.db.query(SearchLog)
            .filter(
                and_(
                    func.date(SearchLog.searched_at) == target_date,
                    SearchLog.clicked_event_id.isnot(None),
                )
            )
            .count()
        )

        metrics.search_success_rate = (
            (successful_searches / metrics.total_searches * 100)
            if metrics.total_searches > 0
            else 0
        )

        self.db.commit()

    # Analytics Queries
    def get_event_analytics(
        self,
        event_id: int,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
    ) -> Dict[str, Any]:
        """Get comprehensive analytics for a specific event."""

        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()

        # Get aggregated metrics
        metrics = (
            self.db.query(EventPerformanceMetrics)
            .filter(
                and_(
                    EventPerformanceMetrics.event_id == event_id,
                    EventPerformanceMetrics.date >= date_from,
                    EventPerformanceMetrics.date <= date_to,
                )
            )
            .order_by(EventPerformanceMetrics.date)
            .all()
        )

        # Calculate totals
        total_views = sum(m.total_views for m in metrics)
        total_unique_views = sum(m.unique_views for m in metrics)
        total_favorites = sum(m.total_favorites for m in metrics)
        total_shares = sum(m.total_shares for m in metrics)

        # Calculate averages
        avg_bounce_rate = (
            sum(m.bounce_rate for m in metrics) / len(metrics) if metrics else 0
        )
        avg_view_duration = (
            sum(m.avg_view_duration for m in metrics) / len(metrics) if metrics else 0
        )

        return {
            "event_id": event_id,
            "date_from": date_from,
            "date_to": date_to,
            "summary": {
                "total_views": total_views,
                "unique_views": total_unique_views,
                "favorites": total_favorites,
                "shares": total_shares,
                "avg_bounce_rate": round(avg_bounce_rate, 2),
                "avg_view_duration": round(avg_view_duration, 2),
            },
            "daily_metrics": [
                {
                    "date": m.date.date(),
                    "views": m.total_views,
                    "unique_views": m.unique_views,
                    "bounce_rate": m.bounce_rate,
                    "avg_duration": m.avg_view_duration,
                }
                for m in metrics
            ],
        }

    def get_popular_events(
        self,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Get most popular events by view count."""

        if not date_from:
            date_from = date.today() - timedelta(days=7)
        if not date_to:
            date_to = date.today()

        popular = (
            self.db.query(
                EventPerformanceMetrics.event_id,
                func.sum(EventPerformanceMetrics.total_views).label("total_views"),
                func.sum(EventPerformanceMetrics.unique_views).label("unique_views"),
            )
            .filter(
                and_(
                    EventPerformanceMetrics.date >= date_from,
                    EventPerformanceMetrics.date <= date_to,
                )
            )
            .group_by(EventPerformanceMetrics.event_id)
            .order_by(desc("total_views"))
            .limit(limit)
            .all()
        )

        result = []
        for event_id, total_views, unique_views in popular:
            event = self.db.query(Event).filter(Event.id == event_id).first()
            if event:
                result.append(
                    {
                        "event_id": event_id,
                        "event_name": event.title,
                        "total_views": total_views,
                        "unique_views": unique_views,
                    }
                )

        return result

    def get_search_analytics(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get search analytics and popular queries."""

        if not date_from:
            date_from = date.today() - timedelta(days=7)
        if not date_to:
            date_to = date.today()

        # Popular search queries
        popular_queries = (
            self.db.query(
                SearchLog.query,
                func.count(SearchLog.id).label("search_count"),
                func.avg(SearchLog.results_count).label("avg_results"),
            )
            .filter(
                and_(
                    func.date(SearchLog.searched_at) >= date_from,
                    func.date(SearchLog.searched_at) <= date_to,
                )
            )
            .group_by(SearchLog.query)
            .order_by(desc("search_count"))
            .limit(20)
            .all()
        )

        # Search success metrics
        total_searches = (
            self.db.query(SearchLog)
            .filter(
                and_(
                    func.date(SearchLog.searched_at) >= date_from,
                    func.date(SearchLog.searched_at) <= date_to,
                )
            )
            .count()
        )

        successful_searches = (
            self.db.query(SearchLog)
            .filter(
                and_(
                    func.date(SearchLog.searched_at) >= date_from,
                    func.date(SearchLog.searched_at) <= date_to,
                    SearchLog.clicked_event_id.isnot(None),
                )
            )
            .count()
        )

        success_rate = (
            (successful_searches / total_searches * 100) if total_searches > 0 else 0
        )

        return {
            "date_from": date_from,
            "date_to": date_to,
            "total_searches": total_searches,
            "successful_searches": successful_searches,
            "success_rate": round(success_rate, 2),
            "popular_queries": [
                {
                    "query": query,
                    "search_count": count,
                    "avg_results": round(avg_results, 1),
                }
                for query, count, avg_results in popular_queries
            ],
        }

    def segment_users(
        self,
        algorithm: str = "kmeans",
        n_clusters: int = 3,
    ) -> Dict[int, List[int]]:
        """Cluster users into segments based on interaction metrics."""

        views_subq = (
            self.db.query(
                EventView.user_id.label("user_id"),
                func.count(EventView.id).label("views"),
            )
            .filter(EventView.user_id.isnot(None))
            .group_by(EventView.user_id)
            .subquery()
        )

        interactions_subq = (
            self.db.query(
                UserInteraction.user_id.label("user_id"),
                func.sum(
                    case(
                        (UserInteraction.interaction_type == "favorite", 1),
                        else_=0,
                    )
                ).label("favorites"),
                func.sum(
                    case(
                        (UserInteraction.interaction_type == "share", 1),
                        else_=0,
                    )
                ).label("shares"),
                func.count(UserInteraction.id).label("interactions"),
            )
            .filter(UserInteraction.user_id.isnot(None))
            .group_by(UserInteraction.user_id)
            .subquery()
        )

        searches_subq = (
            self.db.query(
                SearchLog.user_id.label("user_id"),
                func.count(SearchLog.id).label("searches"),
            )
            .filter(SearchLog.user_id.isnot(None))
            .group_by(SearchLog.user_id)
            .subquery()
        )

        rows = (
            self.db.query(
                User.id.label("user_id"),
                func.coalesce(views_subq.c.views, 0).label("views"),
                func.coalesce(interactions_subq.c.favorites, 0).label("favorites"),
                func.coalesce(interactions_subq.c.shares, 0).label("shares"),
                func.coalesce(interactions_subq.c.interactions, 0).label(
                    "interactions"
                ),
                func.coalesce(searches_subq.c.searches, 0).label("searches"),
            )
            .outerjoin(views_subq, views_subq.c.user_id == User.id)
            .outerjoin(interactions_subq, interactions_subq.c.user_id == User.id)
            .outerjoin(searches_subq, searches_subq.c.user_id == User.id)
            .all()
        )

        if not rows:
            return {}

        df = pd.DataFrame(
            rows,
            columns=[
                "user_id",
                "views",
                "favorites",
                "shares",
                "interactions",
                "searches",
            ],
        )

        features = df.drop("user_id", axis=1).fillna(0)
        scaler = StandardScaler()
        data = scaler.fit_transform(features)

        if algorithm == "dbscan":
            model = DBSCAN(eps=0.5, min_samples=5)
            labels = model.fit_predict(data)
        else:
            model = KMeans(n_clusters=n_clusters, n_init=10)
            labels = model.fit_predict(data)

        df["segment"] = labels

        segments: Dict[int, List[int]] = {}
        for user_id, label in df[["user_id", "segment"]].itertuples(index=False):
            segments.setdefault(int(label), []).append(int(user_id))

        return segments


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service instance."""
    return AnalyticsService(db)
