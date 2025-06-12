from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.analytics import AnalyticsService, get_analytics_service
from ..core.auth import get_current_active_user
from ..core.database import get_db
from ..models.analytics import EventView, SearchLog, UserInteraction
from ..models.user import User

router = APIRouter(prefix="/analytics", tags=["analytics"])


# Pydantic models for requests/responses
class EventViewRequest(BaseModel):
    event_id: int
    session_id: Optional[str] = None
    referrer: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    device_type: Optional[str] = None


class SearchTrackingRequest(BaseModel):
    query: str
    results_count: int
    session_id: Optional[str] = None
    filters: Optional[Dict] = None
    language: Optional[str] = None
    source: Optional[str] = None


class UserInteractionRequest(BaseModel):
    interaction_type: str
    entity_type: str
    entity_id: int
    session_id: Optional[str] = None
    context: Optional[Dict] = None
    value: Optional[str] = None


class EngagementUpdateRequest(BaseModel):
    view_duration: int
    is_bounce: bool = False


class SearchClickRequest(BaseModel):
    clicked_event_id: int
    click_position: int


# Tracking endpoints (for frontend to call)
@router.post("/track/event-view", response_model=None)
def track_event_view(
    view_data: EventViewRequest,
    request: Request,
    db: Session = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_active_user),
) -> Dict[str, Any]:
    """Track an event view with metadata."""

    # Extract IP and user agent from request
    ip_address = request.client.host
    user_agent = request.headers.get("user-agent")

    # Extract geographic info (would need IP geolocation service)
    # For now, we'll leave country/city as None

    view = analytics.track_event_view(
        event_id=view_data.event_id,
        user_id=current_user.id if current_user else None,
        session_id=view_data.session_id,
        ip_address=ip_address,
        user_agent=user_agent,
        referrer=view_data.referrer,
        source=view_data.source,
        language=view_data.language,
        device_type=view_data.device_type,
    )

    return {"view_id": view.id, "tracked": True}


@router.put("/track/event-view/{view_id}/engagement")
def update_view_engagement(
    view_id: int,
    engagement_data: EngagementUpdateRequest,
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Update engagement metrics for a view."""

    analytics.update_view_engagement(
        view_id=view_id,
        view_duration=engagement_data.view_duration,
        is_bounce=engagement_data.is_bounce,
    )

    return {"updated": True}


@router.post("/track/search")
def track_search(
    search_data: SearchTrackingRequest,
    db: Session = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_active_user),
):
    """Track a search query."""

    search_log = analytics.track_search(
        query=search_data.query,
        results_count=search_data.results_count,
        user_id=current_user.id if current_user else None,
        session_id=search_data.session_id,
        filters=search_data.filters,
        language=search_data.language,
        source=search_data.source,
    )

    return {"search_id": search_log.id, "tracked": True}


@router.put("/track/search/{search_id}/click")
def track_search_click(
    search_id: int,
    click_data: SearchClickRequest,
    analytics: AnalyticsService = Depends(get_analytics_service),
):
    """Track when a user clicks on a search result."""

    analytics.track_search_click(
        search_log_id=search_id,
        clicked_event_id=click_data.clicked_event_id,
        click_position=click_data.click_position,
    )

    return {"tracked": True}


@router.post("/track/interaction")
def track_user_interaction(
    interaction_data: UserInteractionRequest,
    db: Session = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
    current_user: Optional[User] = Depends(get_current_active_user),
):
    """Track user interactions."""

    interaction = analytics.track_user_interaction(
        interaction_type=interaction_data.interaction_type,
        entity_type=interaction_data.entity_type,
        entity_id=interaction_data.entity_id,
        user_id=current_user.id if current_user else None,
        session_id=interaction_data.session_id,
        context=interaction_data.context,
        value=interaction_data.value,
    )

    return {"interaction_id": interaction.id, "tracked": True}


# Analytics data endpoints (for admin dashboard)
@router.get("/events/{event_id}")
def get_event_analytics(
    event_id: int,
    date_from: Optional[date] = Query(None, description="Start date for analytics"),
    date_to: Optional[date] = Query(None, description="End date for analytics"),
    db: Session = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get comprehensive analytics for a specific event."""

    # Check if user has permission to view analytics
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return analytics.get_event_analytics(
        event_id=event_id, date_from=date_from, date_to=date_to
    )


@router.get("/popular-events")
def get_popular_events(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    limit: int = Query(10, ge=1, le=50, description="Number of events to return"),
    db: Session = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get most popular events by view count."""

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return analytics.get_popular_events(
        date_from=date_from, date_to=date_to, limit=limit
    )


@router.get("/search-analytics")
def get_search_analytics(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_active_user),
):
    """Get search analytics and popular queries."""

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    return analytics.get_search_analytics(date_from=date_from, date_to=date_to)


@router.get("/platform-overview")
def get_platform_overview(
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get platform-wide analytics overview."""

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

    # Get platform metrics from database
    from ..models.analytics import PlatformMetrics

    metrics = (
        db.query(PlatformMetrics)
        .filter(
            PlatformMetrics.date >= date_from,
            PlatformMetrics.date <= date_to,
            PlatformMetrics.metric_type == "daily",
        )
        .order_by(PlatformMetrics.date)
        .all()
    )

    if not metrics:
        return {
            "date_from": date_from,
            "date_to": date_to,
            "message": "No metrics available for the specified period",
        }

    # Calculate totals and averages
    latest_metrics = metrics[-1] if metrics else None
    total_page_views = sum(m.total_page_views for m in metrics)
    total_searches = sum(m.total_searches for m in metrics)
    avg_bounce_rate = sum(m.bounce_rate for m in metrics) / len(metrics)

    return {
        "date_from": date_from,
        "date_to": date_to,
        "summary": {
            "total_users": latest_metrics.total_users if latest_metrics else 0,
            "total_events": latest_metrics.total_events if latest_metrics else 0,
            "featured_events": latest_metrics.featured_events if latest_metrics else 0,
            "total_page_views": total_page_views,
            "total_searches": total_searches,
            "avg_bounce_rate": round(avg_bounce_rate, 2),
        },
        "daily_metrics": [
            {
                "date": m.date.date(),
                "new_users": m.new_users,
                "active_users": m.active_users,
                "page_views": m.total_page_views,
                "searches": m.total_searches,
                "bounce_rate": m.bounce_rate,
            }
            for m in metrics
        ],
    }


@router.get("/real-time-stats")
def get_real_time_stats(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_active_user)
):
    """Get real-time platform statistics."""

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    today = date.today()

    # Today's stats
    todays_views = (
        db.query(EventView).filter(func.date(EventView.viewed_at) == today).count()
    )

    todays_searches = (
        db.query(SearchLog).filter(func.date(SearchLog.searched_at) == today).count()
    )

    todays_interactions = (
        db.query(UserInteraction)
        .filter(func.date(UserInteraction.interacted_at) == today)
        .count()
    )

    # Active users (last hour)
    hour_ago = datetime.now() - timedelta(hours=1)
    active_users_last_hour = (
        db.query(EventView.user_id)
        .filter(EventView.viewed_at >= hour_ago, EventView.user_id.isnot(None))
        .distinct()
        .count()
    )

    return {
        "todays_views": todays_views,
        "todays_searches": todays_searches,
        "todays_interactions": todays_interactions,
        "active_users_last_hour": active_users_last_hour,
        "last_updated": datetime.now(),
    }


# Aggregation endpoints (for maintenance tasks)
@router.post("/aggregate/daily/{target_date}")
def trigger_daily_aggregation(
    target_date: date,
    db: Session = Depends(get_db),
    analytics: AnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_active_user),
):
    """Manually trigger daily metrics aggregation."""

    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")

    # Aggregate event metrics
    analytics.aggregate_event_metrics(target_date)

    # Aggregate platform metrics
    analytics.aggregate_platform_metrics(target_date, "daily")

    return {
        "aggregated": True,
        "date": target_date,
        "message": f"Daily metrics aggregated for {target_date}",
    }
