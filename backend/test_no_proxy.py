#!/usr/bin/env python3
"""
Test Croatia scraper WITHOUT proxy to test basic connectivity.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.scraping.croatia_scraper import CroatiaScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_no_proxy():
    """Test Croatia scraper without proxy."""
    logger.info("🕷️ Testing Croatia scraper WITHOUT proxy...")
    
    try:
        # Manually patch the scraper configuration to disable proxy
        import app.scraping.croatia_scraper as scraper_module
        
        # Disable proxy
        scraper_module.USE_PROXY = False
        scraper_module.USE_PLAYWRIGHT = True
        
        logger.info(f"Scraper configuration:")
        logger.info(f"  • Use Proxy: {scraper_module.USE_PROXY}")
        logger.info(f"  • Use Playwright: {scraper_module.USE_PLAYWRIGHT}")
        
        # Create scraper instance
        scraper = CroatiaScraper()
        
        # Run scraper with very limited scope for testing
        logger.info("Running scraper (1 page, no details, no proxy)...")
        events = await scraper.scrape_events(max_pages=1, fetch_details=False)
        
        logger.info(f"Scraped {len(events)} events from Croatia.hr")
        
        if events:
            logger.info("Sample scraped events:")
            for i, event in enumerate(events[:3], 1):
                logger.info(f"  {i}. {event.title}")
                logger.info(f"     📅 {event.date} at {event.time}")
                logger.info(f"     📍 {event.location}")
                logger.info(f"     💰 {event.price}")
                if event.link:
                    logger.info(f"     🔗 {event.link}")
                logger.info("")
        else:
            logger.warning("No events were scraped")
        
        logger.info(f"✅ Test completed!")
        logger.info(f"  • Scraped events: {len(events)}")
        
        return len(events) > 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Testing Croatia Scraper WITHOUT Proxy")
    logger.info("=" * 50)
    
    success = await test_no_proxy()
    
    logger.info("=" * 50)
    if success:
        logger.info("🎉 Test completed successfully!")
    else:
        logger.error("❌ Test failed!")
    
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