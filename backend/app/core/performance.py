"""
Performance optimization service with caching and query optimization.
"""

import logging
import time
from datetime import date, datetime, timedelta
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import Depends
from sqlalchemy import and_, asc, desc, func, or_, text
from sqlalchemy.orm import Session, joinedload, selectinload

from ..models.analytics import EventPerformanceMetrics, PlatformMetrics
from ..models.category import EventCategory
from ..models.event import Event
from ..models.translation import EventTranslation
from ..models.user import User
from ..models.venue import Venue
from .cache import cache_invalidate_on_change, cached, get_cache_service
from .database import get_db

logger = logging.getLogger(__name__)


class QueryOptimizer:
    """Query optimization utilities for common database operations."""

    @staticmethod
    def prefetch_relationships(query, model_class, relationships: List[str]):
        """Add eager loading for specified relationships."""
        for rel in relationships:
            if hasattr(model_class, rel):
                query = query.options(joinedload(getattr(model_class, rel)))
        return query

    @staticmethod
    def optimize_event_query(query, include_analytics: bool = False):
        """Optimize event queries with common eager loading."""
        query = query.options(
            joinedload(Event.category),
            joinedload(Event.venue),
            selectinload(Event.translations),
        )

        if include_analytics:
            query = query.options(selectinload(Event.performance_metrics))

        return query

    @staticmethod
    def add_geographic_optimization(
        query, latitude: float, longitude: float, radius_km: float
    ):
        """Add optimized geographic filtering."""
        # Use PostgreSQL's earthdistance extension for performance
        return query.filter(
            func.earth_distance(
                func.ll_to_earth(Event.latitude, Event.longitude),
                func.ll_to_earth(latitude, longitude),
            )
            <= radius_km * 1000
        ).order_by(
            func.earth_distance(
                func.ll_to_earth(Event.latitude, Event.longitude),
                func.ll_to_earth(latitude, longitude),
            )
        )

    @staticmethod
    def add_date_range_optimization(
        query, date_from: Optional[date], date_to: Optional[date]
    ):
        """Add optimized date range filtering."""
        if date_from and date_to:
            # Use index-friendly range query
            return query.filter(Event.date.between(date_from, date_to))
        elif date_from:
            return query.filter(Event.date >= date_from)
        elif date_to:
            return query.filter(Event.date <= date_to)
        return query

    @staticmethod
    def add_search_optimization(query, search_term: str):
        """Add optimized full-text search."""
        if search_term:
            # Use PostgreSQL full-text search index
            return query.filter(Event.search_vector.match(search_term))
        return query


class PerformanceService:
    """Comprehensive performance optimization service."""

    def __init__(self, db: Session):
        self.db = db
        self.cache = get_cache_service()
        self.optimizer = QueryOptimizer()

    # Event-related cached operations
    @cached("events", ttl=1800)  # 30 minutes
    def get_events_optimized(
        self,
        page: int = 1,
        size: int = 20,
        category_id: Optional[int] = None,
        venue_id: Optional[int] = None,
        city: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        is_featured: Optional[bool] = None,
        language: str = "hr",
    ) -> Dict[str, Any]:
        """Get events with optimized caching and queries."""

        # Build optimized query
        query = self.db.query(Event)
        query = self.optimizer.optimize_event_query(query)

        # Apply filters
        if category_id:
            query = query.filter(Event.category_id == category_id)

        if venue_id:
            query = query.filter(Event.venue_id == venue_id)

        if city:
            query = query.filter(Event.location.ilike(f"%{city}%"))

        query = self.optimizer.add_date_range_optimization(query, date_from, date_to)

        if is_featured is not None:
            query = query.filter(Event.is_featured == is_featured)

        # Filter active events
        query = query.filter(Event.event_status == "active")

        # Get total count
        total = query.count()

        # Apply pagination with ordering
        skip = (page - 1) * size
        events = (
            query.order_by(Event.is_featured.desc(), Event.date.asc(), Event.time.asc())
            .offset(skip)
            .limit(size)
            .all()
        )

        # Apply translations if needed
        if language != "hr":
            events = self._apply_translations(events, language)

        return {
            "events": [self._serialize_event(event) for event in events],
            "total": total,
            "page": page,
            "size": len(events),
            "pages": (total + size - 1) // size if total > 0 else 0,
        }

    @cached("event_detail", ttl=3600)  # 1 hour
    def get_event_detail_optimized(
        self, event_id: int, language: str = "hr"
    ) -> Optional[Dict[str, Any]]:
        """Get single event with full details and caching."""

        query = self.db.query(Event).options(
            joinedload(Event.category),
            joinedload(Event.venue),
            selectinload(Event.translations),
            selectinload(Event.favorited_by),
        )

        event = query.filter(Event.id == event_id).first()

        if not event:
            return None

        # Increment view count asynchronously (not cached)
        self._increment_view_count(event_id)

        # Apply translations
        if language != "hr":
            event = self._apply_single_translation(event, language)

        return self._serialize_event_detail(event)

    @cached("popular_events", ttl=900)  # 15 minutes
    def get_popular_events_optimized(
        self, limit: int = 10, days: int = 7, language: str = "hr"
    ) -> List[Dict[str, Any]]:
        """Get popular events based on view counts and metrics."""

        # Get events with high view counts or recent popularity
        cutoff_date = date.today() - timedelta(days=days)

        query = (
            self.db.query(Event)
            .options(joinedload(Event.category), joinedload(Event.venue))
            .filter(Event.event_status == "active", Event.date >= cutoff_date)
            .order_by(desc(Event.view_count), desc(Event.created_at))
            .limit(limit)
        )

        events = query.all()

        if language != "hr":
            events = self._apply_translations(events, language)

        return [self._serialize_event(event) for event in events]

    @cached("categories", ttl=7200)  # 2 hours
    def get_categories_optimized(self, language: str = "hr") -> List[Dict[str, Any]]:
        """Get all categories with caching."""

        query = self.db.query(EventCategory).filter(EventCategory.is_active == True)

        if language != "hr":
            query = query.options(selectinload(EventCategory.translations))

        categories = query.order_by(EventCategory.name).all()

        return [self._serialize_category(cat, language) for cat in categories]

    @cached("venues", ttl=7200)  # 2 hours
    def get_venues_optimized(
        self, city: Optional[str] = None, language: str = "hr"
    ) -> List[Dict[str, Any]]:
        """Get venues with caching."""

        query = self.db.query(Venue).filter(Venue.is_active == True)

        if city:
            query = query.filter(Venue.city.ilike(f"%{city}%"))

        if language != "hr":
            query = query.options(selectinload(Venue.translations))

        venues = query.order_by(Venue.name).all()

        return [self._serialize_venue(venue, language) for venue in venues]

    @cached("search_results", ttl=600)  # 10 minutes
    def search_events_optimized(
        self,
        query_text: str,
        filters: Dict[str, Any] = None,
        page: int = 1,
        size: int = 20,
        language: str = "hr",
    ) -> Dict[str, Any]:
        """Optimized event search with caching."""

        # Build search query
        query = self.db.query(Event)
        query = self.optimizer.optimize_event_query(query)
        query = self.optimizer.add_search_optimization(query, query_text)

        # Apply additional filters
        if filters:
            if filters.get("category_id"):
                query = query.filter(Event.category_id == filters["category_id"])

            if filters.get("city"):
                query = query.filter(Event.location.ilike(f"%{filters['city']}%"))

            if filters.get("date_from") or filters.get("date_to"):
                query = self.optimizer.add_date_range_optimization(
                    query, filters.get("date_from"), filters.get("date_to")
                )

        # Filter active events
        query = query.filter(Event.event_status == "active")

        # Get total and paginated results
        total = query.count()
        skip = (page - 1) * size

        events = (
            query.order_by(
                desc(Event.is_featured),
                desc(
                    func.ts_rank(Event.search_vector, func.plainto_tsquery(query_text))
                ),
                Event.date.asc(),
            )
            .offset(skip)
            .limit(size)
            .all()
        )

        if language != "hr":
            events = self._apply_translations(events, language)

        return {
            "events": [self._serialize_event(event) for event in events],
            "total": total,
            "page": page,
            "size": len(events),
            "pages": (total + size - 1) // size if total > 0 else 0,
            "query": query_text,
            "filters": filters or {},
        }

    @cached("analytics", ttl=1800)  # 30 minutes
    def get_analytics_optimized(
        self, date_from: Optional[date] = None, date_to: Optional[date] = None
    ) -> Dict[str, Any]:
        """Get platform analytics with caching."""

        if not date_from:
            date_from = date.today() - timedelta(days=30)
        if not date_to:
            date_to = date.today()

        # Get platform metrics
        platform_metrics = (
            self.db.query(PlatformMetrics)
            .filter(
                PlatformMetrics.date >= date_from,
                PlatformMetrics.date <= date_to,
                PlatformMetrics.metric_type == "daily",
            )
            .order_by(PlatformMetrics.date)
            .all()
        )

        # Get event performance metrics
        event_metrics = (
            self.db.query(
                func.sum(EventPerformanceMetrics.total_views).label("total_views"),
                func.sum(EventPerformanceMetrics.unique_views).label("unique_views"),
                func.avg(EventPerformanceMetrics.bounce_rate).label("avg_bounce_rate"),
            )
            .filter(
                EventPerformanceMetrics.date >= date_from,
                EventPerformanceMetrics.date <= date_to,
            )
            .first()
        )

        return {
            "date_range": {"from": date_from, "to": date_to},
            "platform_metrics": [
                self._serialize_platform_metric(m) for m in platform_metrics
            ],
            "event_summary": {
                "total_views": event_metrics.total_views or 0,
                "unique_views": event_metrics.unique_views or 0,
                "avg_bounce_rate": (
                    float(event_metrics.avg_bounce_rate)
                    if event_metrics.avg_bounce_rate
                    else 0
                ),
            },
        }

    # Cache invalidation methods
    @cache_invalidate_on_change(
        ["events", "event_detail", "popular_events", "search_results"]
    )
    def create_event(self, event_data: Dict[str, Any]) -> Event:
        """Create event with cache invalidation."""
        event = Event(**event_data)
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    @cache_invalidate_on_change(
        ["events", "event_detail", "popular_events", "search_results"]
    )
    def update_event(
        self, event_id: int, update_data: Dict[str, Any]
    ) -> Optional[Event]:
        """Update event with cache invalidation."""
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if event:
            for key, value in update_data.items():
                setattr(event, key, value)
            self.db.commit()
            self.db.refresh(event)
        return event

    @cache_invalidate_on_change(
        ["events", "event_detail", "popular_events", "search_results"]
    )
    def delete_event(self, event_id: int) -> bool:
        """Delete event with cache invalidation."""
        event = self.db.query(Event).filter(Event.id == event_id).first()
        if event:
            self.db.delete(event)
            self.db.commit()
            return True
        return False

    @cache_invalidate_on_change(["categories"])
    def update_category(
        self, category_id: int, update_data: Dict[str, Any]
    ) -> Optional[EventCategory]:
        """Update category with cache invalidation."""
        category = (
            self.db.query(EventCategory).filter(EventCategory.id == category_id).first()
        )
        if category:
            for key, value in update_data.items():
                setattr(category, key, value)
            self.db.commit()
            self.db.refresh(category)
        return category

    # Private helper methods
    def _increment_view_count(self, event_id: int):
        """Increment view count without affecting cache."""
        try:
            self.db.execute(
                text(
                    "UPDATE events SET view_count = COALESCE(view_count, 0) + 1 WHERE id = :event_id"
                ),
                {"event_id": event_id},
            )
            self.db.commit()
        except Exception as e:
            logger.error(f"Failed to increment view count for event {event_id}: {e}")
            self.db.rollback()

    def _apply_translations(self, events: List[Event], language: str) -> List[Event]:
        """Apply translations to a list of events."""
        # This would integrate with the translation service
        # For now, return events as-is
        return events

    def _apply_single_translation(self, event: Event, language: str) -> Event:
        """Apply translation to a single event."""
        # This would integrate with the translation service
        return event

    def _serialize_event(self, event: Event) -> Dict[str, Any]:
        """Serialize event for JSON response."""
        return {
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "date": event.date.isoformat() if event.date else None,
            "time": event.time,
            "location": event.location,
            "price": event.price,
            "image": event.image,
            "link": event.link,
            "is_featured": event.is_featured,
            "view_count": event.view_count,
            "category": (
                {"id": event.category.id, "name": event.category.name}
                if event.category
                else None
            ),
            "venue": (
                {
                    "id": event.venue.id,
                    "name": event.venue.name,
                    "city": event.venue.city,
                }
                if event.venue
                else None
            ),
        }

    def _serialize_event_detail(self, event: Event) -> Dict[str, Any]:
        """Serialize event with full details."""
        base_data = self._serialize_event(event)
        base_data.update(
            {
                "organizer": event.organizer,
                "contact_info": event.contact_info,
                "tags": event.tags,
                "latitude": float(event.latitude) if event.latitude else None,
                "longitude": float(event.longitude) if event.longitude else None,
                "created_at": (
                    event.created_at.isoformat() if event.created_at else None
                ),
                "updated_at": (
                    event.updated_at.isoformat() if event.updated_at else None
                ),
            }
        )
        return base_data

    def _serialize_category(
        self, category: EventCategory, language: str
    ) -> Dict[str, Any]:
        """Serialize category for JSON response."""
        return {
            "id": category.id,
            "name": category.name,
            "description": category.description,
            "slug": category.slug,
            "icon": category.icon,
            "color": category.color,
            "is_active": category.is_active,
        }

    def _serialize_venue(self, venue: Venue, language: str) -> Dict[str, Any]:
        """Serialize venue for JSON response."""
        return {
            "id": venue.id,
            "name": venue.name,
            "address": venue.address,
            "city": venue.city,
            "country": venue.country,
            "latitude": float(venue.latitude) if venue.latitude else None,
            "longitude": float(venue.longitude) if venue.longitude else None,
            "capacity": venue.capacity,
            "venue_type": venue.venue_type,
            "is_active": venue.is_active,
        }

    def _serialize_platform_metric(self, metric: PlatformMetrics) -> Dict[str, Any]:
        """Serialize platform metric for JSON response."""
        return {
            "date": metric.date.date().isoformat(),
            "total_users": metric.total_users,
            "new_users": metric.new_users,
            "active_users": metric.active_users,
            "total_events": metric.total_events,
            "total_page_views": metric.total_page_views,
            "bounce_rate": float(metric.bounce_rate) if metric.bounce_rate else 0,
        }

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics."""
        cache_stats = self.cache.get_stats()

        # Get database performance stats
        from .database import get_db_pool_status

        db_stats = get_db_pool_status()

        return {
            "cache": cache_stats,
            "database": db_stats,
            "optimization_status": {
                "caching_enabled": self.cache.is_available,
                "query_optimization_enabled": True,
                "performance_monitoring_enabled": True,
            },
        }


def get_performance_service(db: Session = Depends(get_db)) -> PerformanceService:
    """Dependency to get performance service instance."""
    return PerformanceService(db)
