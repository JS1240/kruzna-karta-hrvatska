"""
Simple task scheduler for automated scraping.
For production, consider using Celery with Redis/RabbitMQ.
"""

import asyncio
import schedule
import time
from datetime import datetime
from typing import Callable, Any
import threading

from ..scraping.entrio_scraper import scrape_entrio_events
from ..scraping.croatia_scraper import scrape_croatia_events


class SimpleScheduler:
    """Simple background scheduler for running tasks."""
    
    def __init__(self):
        self.running = False
        self.scheduler_thread = None
    
    def start(self):
        """Start the scheduler in a background thread."""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        print("Scheduler started")
    
    def stop(self):
        """Stop the scheduler."""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        print("Scheduler stopped")
    
    def _run_scheduler(self):
        """Run the scheduler loop."""
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def schedule_daily_scraping(self, hour: int = 2, minute: int = 0):
        """Schedule daily scraping at specified time."""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self._daily_scrape_job)
        print(f"Scheduled daily scraping at {hour:02d}:{minute:02d}")
    
    def schedule_hourly_scraping(self):
        """Schedule scraping every hour."""
        schedule.every().hour.do(self._hourly_scrape_job)
        print("Scheduled hourly scraping")
    
    def _daily_scrape_job(self):
        """Daily scraping job (more comprehensive)."""
        print(f"Starting daily scraping job at {datetime.now()}")
        try:
            # Run comprehensive scraping for all sites
            asyncio.run(self._run_all_scraping_tasks(max_pages=10))
        except Exception as e:
            print(f"Daily scraping job failed: {e}")
    
    def _hourly_scrape_job(self):
        """Hourly scraping job (quick check for new events)."""
        print(f"Starting hourly scraping job at {datetime.now()}")
        try:
            # Run quick scraping for all sites
            asyncio.run(self._run_all_scraping_tasks(max_pages=2))
        except Exception as e:
            print(f"Hourly scraping job failed: {e}")
    
    async def _run_all_scraping_tasks(self, max_pages: int):
        """Execute scraping tasks for all supported sites."""
        results = []
        
        # Scrape Entrio.hr
        try:
            entrio_result = await scrape_entrio_events(max_pages=max_pages)
            results.append(("Entrio.hr", entrio_result))
            print(f"Entrio.hr scraping completed: {entrio_result}")
        except Exception as e:
            print(f"Entrio.hr scraping failed: {e}")
            results.append(("Entrio.hr", {"status": "error", "message": str(e)}))
        
        # Scrape Croatia.hr
        try:
            croatia_result = await scrape_croatia_events(max_pages=max_pages)
            results.append(("Croatia.hr", croatia_result))
            print(f"Croatia.hr scraping completed: {croatia_result}")
        except Exception as e:
            print(f"Croatia.hr scraping failed: {e}")
            results.append(("Croatia.hr", {"status": "error", "message": str(e)}))
        
        # Summary
        total_scraped = sum(result[1].get("scraped_events", 0) for _, result in results if result.get("status") == "success")
        total_saved = sum(result[1].get("saved_events", 0) for _, result in results if result.get("status") == "success")
        
        print(f"All sites scraping completed: {total_scraped} events scraped, {total_saved} new events saved")
        return results


# Global scheduler instance
scheduler = SimpleScheduler()


def setup_default_schedule():
    """Set up default scraping schedule."""
    # Daily comprehensive scraping at 2 AM
    scheduler.schedule_daily_scraping(hour=2, minute=0)
    
    # Start the scheduler
    scheduler.start()
    
    print("Default scraping schedule configured:")
    print("- Daily scraping at 02:00 (10 pages per site)")
    print("- Sites: Entrio.hr, Croatia.hr")


def setup_development_schedule():
    """Set up development schedule (more frequent for testing)."""
    # Scrape every hour for development
    scheduler.schedule_hourly_scraping()
    
    # Start the scheduler
    scheduler.start()
    
    print("Development scraping schedule configured:")
    print("- Hourly scraping (2 pages per site)")
    print("- Sites: Entrio.hr, Croatia.hr")


# Startup function to be called from main.py
def start_scheduler(development: bool = False):
    """Start the appropriate scheduler based on environment."""
    if development:
        setup_development_schedule()
    else:
        setup_default_schedule()


# Cleanup function
def stop_scheduler():
    """Stop the scheduler."""
    scheduler.stop()