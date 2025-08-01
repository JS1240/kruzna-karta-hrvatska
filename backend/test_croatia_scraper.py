#!/usr/bin/env python3
"""
Test script for Croatia.hr scraper with new Bright Data configuration.
This script tests the updated scraper to ensure it works with the centralized config.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.scraping.croatia_scraper import scrape_croatia_events
from app.config.components import get_settings
from app.core.database import SessionLocal
from app.models.event import Event

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_configuration():
    """Test that the configuration is properly loaded."""
    logger.info("🔧 Testing configuration...")
    
    try:
        config = get_settings()
        scraping_config = config.scraping
        
        logger.info(f"✅ Configuration loaded successfully")
        logger.info(f"  • Bright Data User: {scraping_config.brightdata_user}")
        logger.info(f"  • Bright Data Port: {scraping_config.brightdata_port}")
        logger.info(f"  • Use Proxy: {scraping_config.use_proxy}")
        logger.info(f"  • Use Playwright: {scraping_config.use_playwright}")
        logger.info(f"  • Scraping Browser URL: {'Set' if scraping_config.scraping_browser_url else 'Not set'}")
        logger.info(f"  • Is WebSocket Endpoint: {scraping_config.is_websocket_endpoint}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False


def test_database_connection():
    """Test database connectivity."""
    logger.info("🗄️ Testing database connection...")
    
    try:
        db = SessionLocal()
        
        # Try to query events table
        event_count = db.query(Event).count()
        logger.info(f"✅ Database connection successful")
        logger.info(f"  • Current events in database: {event_count}")
        
        db.close()
        return True
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return False


async def test_scraper():
    """Test the Croatia scraper with limited scope."""
    logger.info("🕷️ Testing Croatia scraper...")
    
    try:
        # Run scraper with limited scope (1 page, no detail fetching)
        result = await scrape_croatia_events(max_pages=1, fetch_details=False)
        
        if result["status"] == "success":
            logger.info(f"✅ Scraper test successful!")
            logger.info(f"  • Scraped events: {result['scraped_events']}")
            logger.info(f"  • Saved events: {result['saved_events']}")
            logger.info(f"  • Message: {result['message']}")
            return True
        else:
            logger.error(f"❌ Scraper test failed: {result['message']}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Scraper test failed with exception: {e}")
        return False


def verify_saved_events():
    """Verify that events were actually saved to the database."""
    logger.info("🔍 Verifying saved events...")
    
    try:
        db = SessionLocal()
        
        # Query for events from Croatia source
        croatia_events = db.query(Event).filter(Event.source == "croatia").all()
        
        logger.info(f"✅ Found {len(croatia_events)} events from Croatia.hr in database")
        
        if croatia_events:
            # Show details of the first few events
            for i, event in enumerate(croatia_events[:3], 1):
                logger.info(f"  Event {i}: {event.title}")
                logger.info(f"    📅 Date: {event.date}")
                logger.info(f"    📍 Location: {event.location}")
                logger.info(f"    💰 Price: {event.price}")
                logger.info(f"    🔗 Link: {event.link}")
                logger.info("")
        
        db.close()
        return len(croatia_events) > 0
        
    except Exception as e:
        logger.error(f"❌ Event verification failed: {e}")
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting Croatia Scraper Test")
    logger.info("=" * 50)
    
    # Test configuration
    if not test_configuration():
        logger.error("Configuration test failed. Exiting.")
        return False
    
    logger.info("")
    
    # Test database connection
    if not test_database_connection():
        logger.error("Database test failed. Exiting.")
        return False
    
    logger.info("")
    
    # Test scraper
    if not await test_scraper():
        logger.error("Scraper test failed. Exiting.")
        return False
    
    logger.info("")
    
    # Verify saved events
    if not verify_saved_events():
        logger.warning("No events were saved, but scraper ran without errors.")
    
    logger.info("=" * 50)
    logger.info("🎉 All tests completed!")
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        if success:
            logger.info("✅ Test script completed successfully!")
            sys.exit(0)
        else:
            logger.error("❌ Test script failed!")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)