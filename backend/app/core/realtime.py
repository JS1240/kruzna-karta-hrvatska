import logging
from datetime import date, datetime, timedelta
from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models.analytics import AlertThreshold, EventView, MetricAlert
from .analytics import AnalyticsService

logger = logging.getLogger(__name__)


class RealTimeAnalyticsService:
    """Process streaming analytics data and detect anomalies."""

    def __init__(self, db: Session):
        self.db = db
        self.analytics = AnalyticsService(db)
        self.traffic_threshold = self._get_or_create_threshold(
            "traffic_spike", "max", 0
        )
        self.bounce_threshold = self._get_or_create_threshold("bounce_rate", "max", 0)

    def _get_or_create_threshold(
        self, metric_name: str, threshold_type: str, value: float
    ) -> AlertThreshold:
        threshold = (
            self.db.query(AlertThreshold)
            .filter(AlertThreshold.metric_name == metric_name)
            .first()
        )
        if not threshold:
            threshold = AlertThreshold(
                metric_name=metric_name,
                threshold_type=threshold_type,
                threshold_value=value,
                is_active=True,
            )
            self.db.add(threshold)
            self.db.commit()
            self.db.refresh(threshold)
        return threshold

    def detect_anomalies(self) -> List[MetricAlert]:
        """Check the last five minutes of data for anomalies."""
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=5)
        baseline_start = now - timedelta(hours=1)

        recent_views = (
            self.db.query(func.count(EventView.id))
            .filter(EventView.viewed_at >= window_start)
            .scalar()
        )
        recent_bounces = (
            self.db.query(func.count(EventView.id))
            .filter(
                EventView.viewed_at >= window_start,
                EventView.is_bounce == True,
            )
            .scalar()
        )
        bounce_rate = (recent_bounces / recent_views * 100) if recent_views else 0

        baseline_views = (
            self.db.query(func.count(EventView.id))
            .filter(
                EventView.viewed_at >= baseline_start,
                EventView.viewed_at < window_start,
            )
            .scalar()
        )
        baseline_bounces = (
            self.db.query(func.count(EventView.id))
            .filter(
                EventView.viewed_at >= baseline_start,
                EventView.viewed_at < window_start,
                EventView.is_bounce == True,
            )
            .scalar()
        )

        baseline_avg_views = baseline_views / 12 if baseline_views else 0
        baseline_bounce_rate = (
            baseline_bounces / baseline_views * 100 if baseline_views else 0
        )

        alerts: List[MetricAlert] = []

        if baseline_avg_views and recent_views > baseline_avg_views * 3:
            alert = MetricAlert(
                threshold_id=self.traffic_threshold.id,
                metric_name="traffic_spike",
                current_value=recent_views,
                threshold_value=baseline_avg_views * 3,
                alert_message=f"Traffic spike: {recent_views} views in last 5m",
                severity="high",
            )
            self.db.add(alert)
            alerts.append(alert)
            logger.warning(alert.alert_message)

        if baseline_bounce_rate and bounce_rate > baseline_bounce_rate * 1.5:
            alert = MetricAlert(
                threshold_id=self.bounce_threshold.id,
                metric_name="bounce_rate",
                current_value=bounce_rate,
                threshold_value=baseline_bounce_rate * 1.5,
                alert_message=f"Abnormal bounce rate {bounce_rate:.2f}% in last 5m",
                severity="medium",
            )
            self.db.add(alert)
            alerts.append(alert)
            logger.warning(alert.alert_message)

        if alerts:
            self.db.commit()
        return alerts

    def aggregate_metrics(self) -> None:
        """Update daily platform metrics for historical records."""
        self.analytics.aggregate_platform_metrics(date.today(), "daily")

    def run(self) -> None:
        self.detect_anomalies()
        self.aggregate_metrics()
