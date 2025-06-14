from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.third_party import verify_api_key
from ..core.analytics import AnalyticsService
from ..models.analytics import PlatformMetrics
from ..models.event import Event
from ..models.schemas import EventResponse

router = APIRouter(prefix="/third-party", tags=["third-party"])


@router.get("/events", response_model=EventResponse)
def third_party_events(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """Return upcoming events for partners."""
    query = db.query(Event).filter(Event.status == "active")
    if date_from:
        query = query.filter(Event.date >= date_from)
    if date_to:
        query = query.filter(Event.date <= date_to)
    total = query.count()
    events = query.order_by(Event.date).offset((page - 1) * size).limit(size).all()
    return EventResponse(total=total, page=page, size=size, events=events)


@router.get("/analytics/summary")
def third_party_platform_summary(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """Return aggregated platform metrics without personal data."""
    if not date_from:
        date_from = date.today() - timedelta(days=30)
    if not date_to:
        date_to = date.today()

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

    latest = metrics[-1]
    total_page_views = sum(m.total_page_views for m in metrics)
    total_searches = sum(m.total_searches for m in metrics)
    avg_bounce_rate = sum(m.bounce_rate for m in metrics) / len(metrics)

    return {
        "date_from": date_from,
        "date_to": date_to,
        "summary": {
            "total_users": latest.total_users,
            "total_events": latest.total_events,
            "featured_events": latest.featured_events,
            "total_page_views": total_page_views,
            "total_searches": total_searches,
            "avg_bounce_rate": round(avg_bounce_rate, 2),
        },
    }


@router.get("/analytics/popular-events")
def third_party_popular_events(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    api_key: str = Depends(verify_api_key),
):
    """Return top events by view count."""
    service = AnalyticsService(db)
    popular = service.get_popular_events(
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )
    return {"results": popular}
