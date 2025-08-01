#!/usr/bin/env python3
"""
Test the geocoding fix in Croatia scraper.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.scraping.croatia_scraper import scrape_croatia_events

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_geocoding_fix():
    """Test Croatia scraper with geocoding functionality."""
    logger.info("🗺️ Testing Croatia scraper with geocoding...")
    
    try:
        # Run scraper with minimal scope for testing
        logger.info("Running scraper (1 page, no details) with geocoding...")
        result = await scrape_croatia_events(max_pages=1, fetch_details=False)
        
        logger.info("Scraper result:")
        logger.info(f"  Status: {result.get('status')}")
        logger.info(f"  Scraped events: {result.get('scraped_events')}")
        logger.info(f"  Saved events: {result.get('saved_events')}")
        logger.info(f"  Message: {result.get('message')}")
        
        if result.get('status') == 'success':
            logger.info("✅ Croatia scraper with geocoding completed successfully!")
            return True
        else:
            logger.error(f"❌ Croatia scraper failed: {result.get('message')}")
            return False
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Testing Croatia Scraper Geocoding Fix")
    logger.info("=" * 50)
    
    success = await test_geocoding_fix()
    
    logger.info("=" * 50)
    if success:
        logger.info("🎉 Geocoding test completed successfully!")
    else:
        logger.error("❌ Geocoding test failed!")
    
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