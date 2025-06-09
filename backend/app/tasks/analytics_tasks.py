from datetime import date, datetime, timedelta
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging
from typing import Optional

from ..core.config import settings
from ..core.analytics import AnalyticsService
from ..models.analytics import EventPerformanceMetrics, PlatformMetrics

logger = logging.getLogger(__name__)


class AnalyticsTaskScheduler:
    """Scheduler for analytics aggregation tasks."""
    
    def __init__(self):
        # Create separate database session for background tasks
        self.engine = create_engine(settings.database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_db_session(self):
        """Get database session for tasks."""
        return self.SessionLocal()
    
    def aggregate_yesterday_metrics(self):
        """Aggregate metrics for yesterday."""
        yesterday = date.today() - timedelta(days=1)
        self.aggregate_daily_metrics(yesterday)
    
    def aggregate_daily_metrics(self, target_date: date):
        """Aggregate daily metrics for a specific date."""
        logger.info(f"Starting daily metrics aggregation for {target_date}")
        
        try:
            with self.get_db_session() as db:
                analytics = AnalyticsService(db)
                
                # Aggregate event metrics
                logger.info(f"Aggregating event metrics for {target_date}")
                analytics.aggregate_event_metrics(target_date)
                
                # Aggregate platform metrics
                logger.info(f"Aggregating platform metrics for {target_date}")
                analytics.aggregate_platform_metrics(target_date, 'daily')
                
                logger.info(f"Daily metrics aggregation completed for {target_date}")
                
        except Exception as e:
            logger.error(f"Error aggregating daily metrics for {target_date}: {str(e)}")
            raise
    
    def aggregate_weekly_metrics(self, target_date: Optional[date] = None):
        """Aggregate weekly metrics."""
        if not target_date:
            # Get the last Sunday (end of last week)
            today = date.today()
            days_since_sunday = today.weekday() + 1
            if days_since_sunday == 7:
                days_since_sunday = 0
            target_date = today - timedelta(days=days_since_sunday)
        
        logger.info(f"Starting weekly metrics aggregation for week ending {target_date}")
        
        try:
            with self.get_db_session() as db:
                analytics = AnalyticsService(db)
                analytics.aggregate_platform_metrics(target_date, 'weekly')
                logger.info(f"Weekly metrics aggregation completed for {target_date}")
                
        except Exception as e:
            logger.error(f"Error aggregating weekly metrics for {target_date}: {str(e)}")
            raise
    
    def aggregate_monthly_metrics(self, target_date: Optional[date] = None):
        """Aggregate monthly metrics."""
        if not target_date:
            # Get the last day of the previous month
            today = date.today()
            first_day_this_month = today.replace(day=1)
            target_date = first_day_this_month - timedelta(days=1)
        
        logger.info(f"Starting monthly metrics aggregation for month ending {target_date}")
        
        try:
            with self.get_db_session() as db:
                analytics = AnalyticsService(db)
                analytics.aggregate_platform_metrics(target_date, 'monthly')
                logger.info(f"Monthly metrics aggregation completed for {target_date}")
                
        except Exception as e:
            logger.error(f"Error aggregating monthly metrics for {target_date}: {str(e)}")
            raise
    
    def cleanup_old_raw_data(self, retention_days: int = 90):
        """Clean up old raw analytics data to save space."""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        logger.info(f"Starting cleanup of raw analytics data older than {cutoff_date}")
        
        try:
            with self.get_db_session() as db:
                from ..models.analytics import EventView, SearchLog, UserInteraction
                
                # Count records to be deleted
                old_views = db.query(EventView).filter(EventView.viewed_at < cutoff_date).count()
                old_searches = db.query(SearchLog).filter(SearchLog.searched_at < cutoff_date).count()
                old_interactions = db.query(UserInteraction).filter(UserInteraction.interacted_at < cutoff_date).count()
                
                logger.info(f"Found {old_views} old event views, {old_searches} old searches, {old_interactions} old interactions")
                
                # Delete old records
                db.query(EventView).filter(EventView.viewed_at < cutoff_date).delete()
                db.query(SearchLog).filter(SearchLog.searched_at < cutoff_date).delete()
                db.query(UserInteraction).filter(UserInteraction.interacted_at < cutoff_date).delete()
                
                db.commit()
                logger.info(f"Cleanup completed: removed {old_views + old_searches + old_interactions} old records")
                
        except Exception as e:
            logger.error(f"Error during raw data cleanup: {str(e)}")
            raise
    
    def generate_analytics_report(self, target_date: Optional[date] = None):
        """Generate daily analytics report."""
        if not target_date:
            target_date = date.today() - timedelta(days=1)
        
        logger.info(f"Generating analytics report for {target_date}")
        
        try:
            with self.get_db_session() as db:
                analytics = AnalyticsService(db)
                
                # Get platform metrics
                platform_metrics = db.query(PlatformMetrics).filter(
                    PlatformMetrics.date == target_date,
                    PlatformMetrics.metric_type == 'daily'
                ).first()
                
                if not platform_metrics:
                    logger.warning(f"No platform metrics found for {target_date}")
                    return
                
                # Get popular events
                popular_events = analytics.get_popular_events(
                    date_from=target_date,
                    date_to=target_date,
                    limit=5
                )
                
                # Get search analytics
                search_analytics = analytics.get_search_analytics(
                    date_from=target_date,
                    date_to=target_date
                )
                
                # Create report data
                report = {
                    "date": target_date,
                    "platform_metrics": {
                        "total_users": platform_metrics.total_users,
                        "new_users": platform_metrics.new_users,
                        "active_users": platform_metrics.active_users,
                        "total_page_views": platform_metrics.total_page_views,
                        "total_searches": platform_metrics.total_searches,
                        "bounce_rate": float(platform_metrics.bounce_rate),
                        "search_success_rate": float(platform_metrics.search_success_rate)
                    },
                    "popular_events": popular_events,
                    "search_metrics": search_analytics
                }
                
                # Here you could send this report via email, Slack, etc.
                logger.info(f"Analytics report generated for {target_date}: {report}")
                
                return report
                
        except Exception as e:
            logger.error(f"Error generating analytics report for {target_date}: {str(e)}")
            raise
    
    def check_metric_alerts(self):
        """Check for metric threshold violations and trigger alerts."""
        logger.info("Checking metric alert thresholds")
        
        try:
            with self.get_db_session() as db:
                from ..models.analytics import AlertThreshold, MetricAlert, PlatformMetrics
                
                # Get active alert thresholds
                active_thresholds = db.query(AlertThreshold).filter(
                    AlertThreshold.is_active == True
                ).all()
                
                today = date.today()
                
                # Get today's platform metrics
                today_metrics = db.query(PlatformMetrics).filter(
                    PlatformMetrics.date == today,
                    PlatformMetrics.metric_type == 'daily'
                ).first()
                
                if not today_metrics:
                    logger.warning(f"No platform metrics found for {today}")
                    return
                
                alerts_triggered = 0
                
                for threshold in active_thresholds:
                    current_value = None
                    
                    # Get current value based on metric name
                    if threshold.metric_name == 'bounce_rate':
                        current_value = float(today_metrics.bounce_rate)
                    elif threshold.metric_name == 'active_users':
                        current_value = today_metrics.active_users
                    elif threshold.metric_name == 'search_success_rate':
                        current_value = float(today_metrics.search_success_rate)
                    elif threshold.metric_name == 'total_page_views':
                        current_value = today_metrics.total_page_views
                    
                    if current_value is None:
                        continue
                    
                    # Check threshold violation
                    threshold_violated = False
                    
                    if threshold.threshold_type == 'min' and current_value < float(threshold.threshold_value):
                        threshold_violated = True
                    elif threshold.threshold_type == 'max' and current_value > float(threshold.threshold_value):
                        threshold_violated = True
                    
                    if threshold_violated:
                        # Check if alert already exists for today
                        existing_alert = db.query(MetricAlert).filter(
                            MetricAlert.threshold_id == threshold.id,
                            MetricAlert.triggered_at >= datetime.combine(today, datetime.min.time()),
                            MetricAlert.is_resolved == False
                        ).first()
                        
                        if not existing_alert:
                            # Create new alert
                            alert_message = f"Metric {threshold.metric_name} violated threshold: {current_value} {threshold.threshold_type} {threshold.threshold_value}"
                            
                            # Determine severity based on how much threshold is violated
                            violation_percentage = abs(current_value - float(threshold.threshold_value)) / float(threshold.threshold_value) * 100
                            
                            if violation_percentage > 50:
                                severity = 'critical'
                            elif violation_percentage > 25:
                                severity = 'high'
                            elif violation_percentage > 10:
                                severity = 'medium'
                            else:
                                severity = 'low'
                            
                            new_alert = MetricAlert(
                                threshold_id=threshold.id,
                                metric_name=threshold.metric_name,
                                current_value=current_value,
                                threshold_value=float(threshold.threshold_value),
                                alert_message=alert_message,
                                severity=severity
                            )
                            
                            db.add(new_alert)
                            alerts_triggered += 1
                            
                            logger.warning(f"Alert triggered: {alert_message} (Severity: {severity})")
                
                db.commit()
                logger.info(f"Metric alert check completed. {alerts_triggered} new alerts triggered.")
                
        except Exception as e:
            logger.error(f"Error checking metric alerts: {str(e)}")
            raise


# Global instance for use in scheduler
analytics_scheduler = AnalyticsTaskScheduler()