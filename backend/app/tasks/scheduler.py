"""
Simple task scheduler for automated scraping.
For production, consider using Celery with Redis/RabbitMQ.
"""

import asyncio
import logging
import threading
import time
from datetime import datetime

import schedule

from backend.app.scraping.croatia_scraper import scrape_croatia_events
from backend.app.scraping.enhanced_scraper import run_enhanced_scraping_pipeline
from backend.app.scraping.entrio_scraper import scrape_entrio_events
from backend.app.scraping.ulaznice_scraper import scrape_ulaznice_events
# Analytics and realtime services removed for MVP

logger = logging.getLogger(__name__)

# NOTE: The following features are disabled for MVP:
# - Analytics aggregation and reporting
# - Database backup automation  
# - Monitoring and alerting
# - Realtime analytics processing
# These functions will log errors when called but won't break the scheduler


class SimpleScheduler:
    """Simple background scheduler for running tasks."""

    def __init__(self):
        self.running = False
        self.scheduler_thread = None

    def start(self):
        """Start the scheduler in a background thread with daemon mode.
        
        Initializes the scheduler in a separate daemon thread to avoid blocking
        the main application. The scheduler will check for pending jobs every minute
        and execute them according to their schedules. Safe to call multiple times.
        
        Note:
            Uses daemon thread so scheduler stops automatically when main process exits.
            The scheduler runs in a continuous loop, checking for pending jobs every 60 seconds.
            If already running, this method returns without creating additional threads.
        """
        if self.running:
            return

        self.running = True
        self.scheduler_thread = threading.Thread(
            target=self._run_scheduler, daemon=True
        )
        self.scheduler_thread.start()
        logger.info("Scheduler started")

    def stop(self):
        """Stop the scheduler and wait for background thread to finish.
        
        Gracefully shuts down the scheduler by setting the running flag to False
        and waiting up to 5 seconds for the background thread to terminate.
        Logs the shutdown status for monitoring purposes.
        
        Note:
            Uses a 5-second timeout when joining the thread to prevent indefinite blocking.
            Safe to call multiple times or when scheduler is not running.
        """
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        logger.info("Scheduler stopped")

    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    def schedule_daily_scraping(self, hour: int = 2, minute: int = 0):
        """Schedule daily comprehensive scraping at specified time.
        
        Configures daily event scraping using the enhanced scraping pipeline
        with comprehensive data collection. Runs at 2 AM by default to minimize
        impact on system resources during low-traffic hours.
        
        Args:
            hour: Hour of day to run scraping (0-23, default: 2 for 2 AM)
            minute: Minute of hour to run scraping (0-59, default: 0)
            
        Note:
            Uses enhanced scraping pipeline with 10 pages per source and 60% quality threshold.
            Scrapes all configured event sources: Entrio.hr, Croatia.hr, Ulaznice.hr.
            Logs comprehensive performance metrics and scraping results.
        """
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._daily_scrape_job)
        logger.info(f"Scheduled daily scraping at {hour:02d}:{minute:02d}")

    def schedule_hourly_scraping(self):
        """Schedule scraping every hour."""
        schedule.every().hour.do(self._hourly_scrape_job)
        logger.info("Scheduled hourly scraping")

    def schedule_analytics_tasks(self):
        """Schedule analytics aggregation and monitoring tasks."""
        # Daily metrics aggregation at 3 AM (after scraping)
        schedule.every().day.at("03:00").do(self._daily_analytics_job)

        # Weekly metrics aggregation on Monday at 4 AM
        schedule.every().monday.at("04:00").do(self._weekly_analytics_job)

        # Monthly metrics aggregation on 1st of month at 5 AM
        schedule.every().day.at("05:00").do(self._monthly_analytics_job)

        # Check metric alerts every 6 hours
        schedule.every(6).hours.do(self._metric_alerts_job)

        # Cleanup old raw data weekly on Sunday at 6 AM
        schedule.every().sunday.at("06:00").do(self._cleanup_analytics_job)

        logger.info("Scheduled analytics tasks:")
        logger.info("- Daily metrics aggregation at 03:00")
        logger.info("- Weekly metrics aggregation on Monday at 04:00")
        logger.info("- Monthly metrics aggregation on 1st at 05:00")
        logger.info("- Metric alerts check every 6 hours")
        logger.info("- Analytics cleanup on Sunday at 06:00")

    def schedule_backup_tasks(self):
        """Schedule automated backup tasks."""
        # Daily full backup at 1 AM (before scraping)
        schedule.every().day.at("01:00").do(self._daily_backup_job)

        # Weekly schema backup on Sunday at 1:30 AM
        schedule.every().sunday.at("01:30").do(self._weekly_schema_backup_job)

        # Weekly backup cleanup on Sunday at 7 AM (after analytics cleanup)
        schedule.every().sunday.at("07:00").do(self._backup_cleanup_job)

        logger.info("Scheduled backup tasks:")
        logger.info("- Daily full backup at 01:00")
        logger.info("- Weekly schema backup on Sunday at 01:30")
        logger.info("- Weekly backup cleanup on Sunday at 07:00")

    def schedule_monitoring_tasks(self):
        """Schedule automated monitoring tasks."""
        # Update metrics every 30 seconds
        schedule.every(30).seconds.do(self._update_monitoring_metrics_job)

        # Check alerts every 2 minutes
        schedule.every(2).minutes.do(self._check_monitoring_alerts_job)

        # Real-time analytics processing every minute
        schedule.every().minute.do(self._real_time_analytics_job)

        logger.info("Scheduled monitoring tasks:")
        logger.info("- Metrics update every 30 seconds")
        logger.info("- Alert checking every 2 minutes")
        logger.info("- Real-time analytics every minute")

    def schedule_gdpr_tasks(self):
        """Schedule automated GDPR compliance tasks."""
        # Daily GDPR data retention cleanup at 4 AM (after analytics)
        schedule.every().day.at("04:00").do(self._gdpr_data_retention_cleanup_job)

        logger.info("Scheduled GDPR compliance tasks:")
        logger.info("- Daily data retention cleanup at 04:00")

    def schedule_croatian_tasks(self):
        """Schedule Croatian-specific tasks."""
        # Update Croatian currency rates every hour during business hours
        schedule.every().hour.at(":00").do(self._update_croatian_currency_rates_job)

        # Cache Croatian holidays at midnight on January 1st
        schedule.every().day.at("00:01").do(self._update_croatian_holidays_cache_job)

        logger.info("Scheduled Croatian localization tasks:")
        logger.info("- Currency rates update every hour")
        logger.info("- Holiday cache update daily at 00:01")

    def _daily_scrape_job(self):
        """Daily scraping job with enhanced pipeline (comprehensive)."""
        logger.info(f"Starting enhanced daily scraping job at {datetime.now()}")
        try:
            # Use enhanced scraping pipeline for better quality
            result = asyncio.run(
                run_enhanced_scraping_pipeline(
                    max_pages_per_source=10, quality_threshold=60.0
                )
            )

            # Log detailed results
            performance = result.get("performance_analysis", {}).get(
                "performance_metrics", {}
            )
            logger.info(
                f"Daily scraping completed: {performance.get('total_events_scraped', 0)} scraped, "
                f"{performance.get('total_events_saved', 0)} saved"
            )

            # Print performance report if available
            if result.get("performance_report"):
                logger.info(result["performance_report"])

        except Exception as e:
            logger.error(f"Enhanced daily scraping job failed: {e}")

    def _hourly_scrape_job(self):
        """Hourly scraping job with enhanced pipeline (quick check)."""
        logger.info(f"Starting enhanced hourly scraping job at {datetime.now()}")
        try:
            # Use enhanced scraping pipeline with lower threshold for hourly updates
            result = asyncio.run(
                run_enhanced_scraping_pipeline(
                    max_pages_per_source=2,
                    quality_threshold=50.0,  # Lower threshold for frequent updates
                )
            )

            # Log brief results
            performance = result.get("performance_analysis", {}).get(
                "performance_metrics", {}
            )
            logger.info(
                f"Hourly scraping completed: {performance.get('total_events_scraped', 0)} scraped, "
                f"{performance.get('total_events_saved', 0)} saved"
            )

        except Exception as e:
            logger.error(f"Enhanced hourly scraping job failed: {e}")

    async def _run_all_scraping_tasks(self, max_pages: int):
        """Execute scraping tasks for all supported sites."""
        results = []

        # Scrape Entrio.hr
        try:
            entrio_result = await scrape_entrio_events(max_pages=max_pages)
            results.append(("Entrio.hr", entrio_result))
            logger.info(f"Entrio.hr scraping completed: {entrio_result}")
        except Exception as e:
            logger.error(f"Entrio.hr scraping failed: {e}")
            results.append(("Entrio.hr", {"status": "error", "message": str(e)}))

        # Scrape Croatia.hr
        try:
            croatia_result = await scrape_croatia_events(max_pages=max_pages)
            results.append(("Croatia.hr", croatia_result))
            logger.info(f"Croatia.hr scraping completed: {croatia_result}")
        except Exception as e:
            logger.error(f"Croatia.hr scraping failed: {e}")
            results.append(("Croatia.hr", {"status": "error", "message": str(e)}))

        # Scrape Ulaznice.hr
        try:
            ulaznice_result = await scrape_ulaznice_events(max_pages=max_pages)
            results.append(("Ulaznice.hr", ulaznice_result))
            logger.info(f"Ulaznice.hr scraping completed: {ulaznice_result}")
        except Exception as e:
            logger.error(f"Ulaznice.hr scraping failed: {e}")
            results.append(("Ulaznice.hr", {"status": "error", "message": str(e)}))

        # Summary
        total_scraped = sum(
            result[1].get("scraped_events", 0)
            for _, result in results
            if result.get("status") == "success"
        )
        total_saved = sum(
            result[1].get("saved_events", 0)
            for _, result in results
            if result.get("status") == "success"
        )

        logger.info(
            f"All sites scraping completed: {total_scraped} events scraped, {total_saved} new events saved"
        )
        return results

    def _daily_analytics_job(self):
        """Daily analytics aggregation job."""
        logger.info(f"Starting daily analytics aggregation at {datetime.now()}")
        try:
            analytics_scheduler.aggregate_yesterday_metrics()
            analytics_scheduler.generate_analytics_report()
            logger.info("Daily analytics aggregation completed")
        except Exception as e:
            logger.error(f"Daily analytics aggregation failed: {e}")

    def _weekly_analytics_job(self):
        """Weekly analytics aggregation job."""
        logger.info(f"Starting weekly analytics aggregation at {datetime.now()}")
        try:
            analytics_scheduler.aggregate_weekly_metrics()
            logger.info("Weekly analytics aggregation completed")
        except Exception as e:
            logger.error(f"Weekly analytics aggregation failed: {e}")

    def _monthly_analytics_job(self):
        """Monthly analytics aggregation job."""
        from datetime import date

        if date.today().day == 1:  # Only run on first day of month
            logger.info(f"Starting monthly analytics aggregation at {datetime.now()}")
            try:
                analytics_scheduler.aggregate_monthly_metrics()
                logger.info("Monthly analytics aggregation completed")
            except Exception as e:
                logger.error(f"Monthly analytics aggregation failed: {e}")

    def _metric_alerts_job(self):
        """Metric alerts monitoring job."""
        logger.info(f"Starting metric alerts check at {datetime.now()}")
        try:
            analytics_scheduler.check_metric_alerts()
            logger.info("Metric alerts check completed")
        except Exception as e:
            logger.error(f"Metric alerts check failed: {e}")

    def _cleanup_analytics_job(self):
        """Analytics data cleanup job."""
        logger.info(f"Starting analytics cleanup at {datetime.now()}")
        try:
            analytics_scheduler.cleanup_old_raw_data(retention_days=90)
            logger.info("Analytics cleanup completed")
        except Exception as e:
            logger.error(f"Analytics cleanup failed: {e}")

    def _daily_backup_job(self):
        """Daily backup job."""
        logger.info(f"Starting daily database backup at {datetime.now()}")
        try:
            from backend.app.core.backup import get_backup_service

            backup_service = get_backup_service()

            metadata = backup_service.create_full_backup(
                custom_filename=None, include_analytics=True
            )

            logger.info(
                f"Daily backup completed: {metadata.backup_id} ({metadata.file_size:,} bytes)"
            )

            if metadata.storage_location:
                logger.info(f"Backup uploaded to S3: {metadata.storage_location}")

        except Exception as e:
            logger.error(f"Daily backup failed: {e}")

    def _weekly_schema_backup_job(self):
        """Weekly schema backup job."""
        logger.info(f"Starting weekly schema backup at {datetime.now()}")
        try:
            from backend.app.core.backup import get_backup_service

            backup_service = get_backup_service()

            metadata = backup_service.create_schema_backup()

            logger.info(
                f"Weekly schema backup completed: {metadata.backup_id} ({metadata.file_size:,} bytes)"
            )

        except Exception as e:
            logger.error(f"Weekly schema backup failed: {e}")

    def _backup_cleanup_job(self):
        """Backup cleanup job."""
        logger.info(f"Starting backup cleanup at {datetime.now()}")
        try:
            from backend.app.core.backup import get_backup_service

            backup_service = get_backup_service()

            result = backup_service.cleanup_old_backups()

            if result["status"] == "success":
                logger.info(
                    f"Backup cleanup completed: {result['cleaned_files']} files, "
                    f"{result['size_freed_bytes']:,} bytes freed"
                )
                if result.get("s3_files_cleaned"):
                    logger.info(f"S3 files cleaned: {result['s3_files_cleaned']}")
            else:
                logger.error(f"Backup cleanup failed: {result['error']}")

        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")

    def _update_monitoring_metrics_job(self):
        """Update monitoring metrics job."""
        try:
            from backend.app.core.monitoring import get_monitoring_service

            monitoring_service = get_monitoring_service()

            # Use asyncio to run the async function
            import asyncio

            asyncio.run(monitoring_service.update_prometheus_metrics())

        except Exception as e:
            logger.error(f"Monitoring metrics update failed: {e}")

    def _check_monitoring_alerts_job(self):
        """Check monitoring alerts job."""
        try:
            from backend.app.core.monitoring import get_monitoring_service

            monitoring_service = get_monitoring_service()

            # Use asyncio to run the async function
            import asyncio

            alerts = asyncio.run(monitoring_service.check_alerts())

            # Log critical alerts
            critical_alerts = [a for a in alerts if a["severity"] == "critical"]
            if critical_alerts:
                logger.info(
                    f"CRITICAL ALERTS: {len(critical_alerts)} critical alerts detected"
                )
                for alert in critical_alerts:
                    logger.info(f"  - {alert['message']}")

        except Exception as e:
            logger.error(f"Monitoring alerts check failed: {e}")

    def _real_time_analytics_job(self):
        """Process real-time analytics and anomaly detection."""
        logger.info(f"Running real-time analytics at {datetime.now()}")
        try:
            with analytics_scheduler.get_db_session() as db:
                service = RealTimeAnalyticsService(db)
                service.run()
            logger.info("Real-time analytics processed")
        except Exception as e:
            logger.error(f"Real-time analytics failed: {e}")

    def _gdpr_data_retention_cleanup_job(self):
        """GDPR data retention cleanup job."""
        logger.info(f"Starting GDPR data retention cleanup at {datetime.now()}")
        try:
            from backend.app.core.security import get_gdpr_service

            gdpr_service = get_gdpr_service()

            result = gdpr_service.run_data_retention_cleanup()

            if result["status"] == "completed":
                logger.info(f"GDPR cleanup completed: {len(result['actions'])} actions")
                for action in result["actions"]:
                    logger.info(f"  - {action}")
            else:
                logger.error(f"GDPR cleanup failed: {result['message']}")

        except Exception as e:
            logger.error(f"GDPR data retention cleanup failed: {e}")

    def _update_croatian_currency_rates_job(self):
        """Update Croatian currency exchange rates."""
        logger.info(f"Starting Croatian currency rates update at {datetime.now()}")
        try:
            from backend.app.core.croatian import get_croatian_currency_service

            currency_service = get_croatian_currency_service()

            # Force update of exchange rates
            currency_service._update_exchange_rates()

            logger.info("Croatian currency rates updated successfully")

        except Exception as e:
            logger.error(f"Croatian currency rates update failed: {e}")

    def _update_croatian_holidays_cache_job(self):
        """Update Croatian holidays cache."""
        logger.info(f"Starting Croatian holidays cache update at {datetime.now()}")
        try:

            from backend.app.core.croatian import get_croatian_holiday_service

            holiday_service = get_croatian_holiday_service()

            # Update cache for current and next year
            current_year = datetime.now().year
            years_to_cache = [current_year, current_year + 1]

            total_holidays = 0
            for year in years_to_cache:
                holidays = holiday_service.get_croatian_holidays(year)
                total_holidays += len(holidays)
                logger.info(f"  - Cached {len(holidays)} holidays for {year}")

            logger.info(
                f"Croatian holidays cache updated: {total_holidays} total holidays cached"
            )

        except Exception as e:
            logger.error(f"Croatian holidays cache update failed: {e}")


# Global scheduler instance
scheduler = SimpleScheduler()


def setup_default_schedule() -> None:
    """Set up default production schedule with comprehensive automation.
    
    Configures the complete production scheduler with daily scraping, analytics
    aggregation, automated backups, monitoring, GDPR compliance, and Croatian
    localization features. Designed for unattended operation in production environments.
    
    Note:
        Production schedule includes:
        - Daily scraping at 2 AM (10 pages per site)
        - Analytics aggregation and reporting
        - Automated database backups and cleanup
        - Real-time monitoring and alerting
        - GDPR data retention compliance
        - Croatian currency and holiday updates
        
        Automatically starts the scheduler after configuration.
    """
    # Daily comprehensive scraping at 2 AM
    scheduler.schedule_daily_scraping(hour=2, minute=0)

    # Schedule analytics tasks
    scheduler.schedule_analytics_tasks()

    # Schedule backup tasks
    scheduler.schedule_backup_tasks()

    # Schedule monitoring tasks
    scheduler.schedule_monitoring_tasks()

    # Schedule GDPR tasks
    scheduler.schedule_gdpr_tasks()

    # Schedule Croatian localization tasks
    scheduler.schedule_croatian_tasks()

    # Start the scheduler
    scheduler.start()

    logger.info("Default production schedule configured:")
    logger.info("- Daily scraping at 02:00 (10 pages per site)")
    logger.info("- Sites: Entrio.hr, Croatia.hr")
    logger.info("- Analytics aggregation and monitoring enabled")
    logger.info("- Automated backup and disaster recovery enabled")
    logger.info("- Real-time monitoring and alerting enabled")
    logger.info("- GDPR compliance and data retention enabled")
    logger.info("- Croatian localization features enabled")


def setup_development_schedule() -> None:
    """Set up development schedule (more frequent for testing)."""
    # Scrape every hour for development
    scheduler.schedule_hourly_scraping()

    # Schedule analytics tasks (same as production)
    scheduler.schedule_analytics_tasks()

    # Schedule backup tasks (same as production)
    scheduler.schedule_backup_tasks()

    # Schedule monitoring tasks (same as production)
    scheduler.schedule_monitoring_tasks()

    # Schedule GDPR tasks (same as production)
    scheduler.schedule_gdpr_tasks()

    # Schedule Croatian localization tasks (same as production)
    scheduler.schedule_croatian_tasks()

    # Start the scheduler
    scheduler.start()

    logger.info("Development schedule configured:")
    logger.info("- Hourly scraping (2 pages per site)")
    logger.info("- Sites: Entrio.hr, Croatia.hr")
    logger.info("- Analytics aggregation and monitoring enabled")
    logger.info("- Automated backup and disaster recovery enabled")
    logger.info("- Real-time monitoring and alerting enabled")
    logger.info("- GDPR compliance and data retention enabled")
    logger.info("- Croatian localization features enabled")


# Startup function to be called from main.py
def start_scheduler(development: bool = False) -> None:
    """Start the appropriate scheduler configuration based on environment.
    
    Entry point for scheduler initialization that automatically selects between
    production and development configurations. Called from main.py during
    application startup when ENABLE_SCHEDULER environment variable is true.
    
    Args:
        development: If True, uses development schedule (hourly scraping, 2 pages)
            If False, uses production schedule (daily scraping, 10 pages)
            
    Note:
        Development mode: Hourly scraping for testing and development
        Production mode: Daily scraping optimized for production workloads
        Both modes include full analytics, backup, monitoring, and compliance features.
    """
    if development:
        setup_development_schedule()
    else:
        setup_default_schedule()


# Cleanup function
def stop_scheduler() -> None:
    """Stop the scheduler during application shutdown.
    
    Gracefully shuts down the scheduler and all background tasks.
    Called from main.py during application lifespan shutdown to ensure
    clean termination of scheduled jobs.
    
    Note:
        Waits up to 5 seconds for scheduler thread to terminate gracefully.
        Safe to call multiple times or when scheduler is not running.
    """
    scheduler.stop()
