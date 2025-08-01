#!/usr/bin/env python3
"""
Manual test script for Croatia.hr scraper to bypass configuration issues.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.scraping.croatia_scraper import CroatiaScraper
from app.core.database import SessionLocal
from app.models.event import Event

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_manual_scraper():
    """Test Croatia scraper with manual configuration."""
    logger.info("🕷️ Testing Croatia scraper with manual config...")
    
    # Get environment variables
    user = os.getenv("BRIGHTDATA_USER", "demo_user")
    password = os.getenv("BRIGHTDATA_PASSWORD", "demo_password")
    port = os.getenv("BRIGHTDATA_PORT", "9222")
    use_scraping_browser = os.getenv("USE_SCRAPING_BROWSER", "")
    
    logger.info(f"Using Bright Data configuration:")
    logger.info(f"  • User: {user}")
    logger.info(f"  • Port: {port}")
    logger.info(f"  • Scraping Browser URL: {'Set' if use_scraping_browser else 'Not set'}")
    
    try:
        # Manually patch the configuration in the scraper module
        import app.scraping.croatia_scraper as scraper_module
        
        # Update the module-level variables
        scraper_module.USER = user
        scraper_module.PASSWORD = password
        scraper_module.BRIGHTDATA_PORT = int(port)
        scraper_module.PROXY = f"http://{user}:{password}@brd.superproxy.io:{port}"
        
        if use_scraping_browser:
            scraper_module.BRD_WSS = use_scraping_browser
            scraper_module.USE_PROXY = True
        else:
            scraper_module.BRD_WSS = f"wss://{user}:{password}@brd.superproxy.io:9222"
            scraper_module.USE_PROXY = bool(user != "demo_user")
        
        logger.info(f"Updated configuration:")
        logger.info(f"  • Proxy: {scraper_module.PROXY}")
        logger.info(f"  • WebSocket: {scraper_module.BRD_WSS}")
        logger.info(f"  • Use Proxy: {scraper_module.USE_PROXY}")
        
        # Create scraper instance
        scraper = CroatiaScraper()
        
        # Get initial event count
        db = SessionLocal()
        initial_count = db.query(Event).filter(Event.source == "croatia").count()
        logger.info(f"Initial Croatia events in database: {initial_count}")
        db.close()
        
        # Run scraper with limited scope
        logger.info("Running scraper (1 page, no details)...")
        events = await scraper.scrape_events(max_pages=1, fetch_details=False)
        
        # Save events
        saved_count = scraper.save_events_to_database(events)
        
        # Get final count
        db = SessionLocal()
        final_count = db.query(Event).filter(Event.source == "croatia").count()
        
        # Show some event details
        if final_count > initial_count:
            logger.info("Showing newly added events:")
            recent_events = db.query(Event).filter(Event.source == "croatia").order_by(Event.created_at.desc()).limit(3)
            for event in recent_events:
                logger.info(f"  📅 {event.title}")
                logger.info(f"    Date: {event.date}, Location: {event.location}")
                logger.info(f"    Price: {event.price}")
                if event.link:
                    logger.info(f"    Link: {event.link}")
                logger.info("")
        
        db.close()
        
        logger.info(f"✅ Scraper completed successfully!")
        logger.info(f"  • Scraped events: {len(events)}")
        logger.info(f"  • Saved events: {saved_count}")
        logger.info(f"  • Total Croatia events: {final_count}")
        
        return len(events) > 0 or saved_count > 0
        
    except Exception as e:
        logger.error(f"❌ Scraper failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting Manual Croatia Scraper Test")
    logger.info("=" * 50)
    
    success = await test_manual_scraper()
    
    logger.info("=" * 50)
    if success:
        logger.info("🎉 Manual test completed successfully!")
    else:
        logger.error("❌ Manual test failed!")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)