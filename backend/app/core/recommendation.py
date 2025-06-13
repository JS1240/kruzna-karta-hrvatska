"""Simple recommendation engine for suggesting events to users."""

from datetime import date
from typing import Any, Dict, List

from fastapi import Depends
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from ..models.analytics import EventView, SearchLog, UserInteraction
from ..models.event import Event
from ..models.user import user_favorites
from .database import get_db
from .performance import PerformanceService


class RecommendationService:
    """Provide event recommendations for a user based on history."""

    def __init__(self, db: Session):
        self.db = db
        self.performance = PerformanceService(db)

    def _get_user_history_event_ids(self, user_id: int) -> List[int]:
        """Collect event ids the user interacted with."""
        viewed = (
            self.db.query(EventView.event_id)
            .filter(EventView.user_id == user_id)
            .distinct()
            .all()
        )
        favorited = (
            self.db.query(user_favorites.c.event_id)
            .filter(user_favorites.c.user_id == user_id)
            .all()
        )
        clicked = (
            self.db.query(SearchLog.clicked_event_id)
            .filter(SearchLog.user_id == user_id, SearchLog.clicked_event_id.isnot(None))
            .all()
        )
        shared = (
            self.db.query(UserInteraction.entity_id)
            .filter(
                UserInteraction.user_id == user_id,
                UserInteraction.entity_type == "event",
                UserInteraction.interaction_type.in_(["share", "favorite"]),
            )
            .all()
        )

        ids = {eid for (eid,) in viewed}
        ids.update(eid for (eid,) in favorited)
        ids.update(eid for (eid,) in clicked)
        ids.update(eid for (eid,) in shared)
        return list(ids)

    def get_recommendations(self, user_id: int, limit: int = 10, language: str = "hr") -> List[Dict[str, Any]]:
        """Return recommended events for the user."""
        history_ids = self._get_user_history_event_ids(user_id)

        if not history_ids:
            # Fallback to popular events if no history
            return self.performance.get_popular_events_optimized(limit=limit, language=language)

        # Determine top categories from history
        category_counts = (
            self.db.query(Event.category_id, func.count(Event.id).label("cnt"))
            .filter(Event.id.in_(history_ids))
            .group_by(Event.category_id)
            .order_by(desc("cnt"))
            .limit(3)
            .all()
        )
        category_ids = [cid for cid, _ in category_counts if cid is not None]

        query = (
            self.db.query(Event)
            .filter(
                Event.category_id.in_(category_ids),
                Event.id.notin_(history_ids),
                Event.event_status == "active",
                Event.date >= date.today(),
            )
            .order_by(desc(Event.view_count), desc(Event.created_at))
            .limit(limit)
        )
        events = query.all()

        if language != "hr":
            events = self.performance._apply_translations(events, language)

        return [self.performance._serialize_event(event) for event in events]


def get_recommendation_service(db: Session = Depends(get_db)) -> RecommendationService:
    return RecommendationService(db)
