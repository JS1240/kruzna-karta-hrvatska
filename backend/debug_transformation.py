#!/usr/bin/env python3
"""
Debug the event transformation process.
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.scraping.croatia_scraper import CroatiaPlaywrightScraper, CroatiaEventDataTransformer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def debug_transformation():
    """Debug the transformation process."""
    logger.info("🔍 Debugging Croatia.hr event transformation...")
    
    try:
        # Disable proxy for testing
        import app.scraping.croatia_scraper as scraper_module
        scraper_module.USE_PROXY = False
        scraper_module.USE_PLAYWRIGHT = True
        
        # Create scraper instance
        playwright_scraper = CroatiaPlaywrightScraper()
        transformer = CroatiaEventDataTransformer()
        
        # Scrape raw data
        logger.info("Scraping raw events (limited to 1 page)...")
        raw_events = await playwright_scraper.scrape_with_playwright(max_pages=1, fetch_details=False)
        
        logger.info(f"Found {len(raw_events)} raw events")
        
        if raw_events:
            # Show first few raw events
            logger.info("First 3 raw events structure:")
            for i, event in enumerate(raw_events[:3], 1):
                logger.info(f"\n--- Raw Event {i} ---")
                logger.info(json.dumps(event, indent=2, ensure_ascii=False))
                
                # Try to transform this event
                logger.info(f"\nTransforming event {i}:")
                try:
                    transformed = transformer.transform_to_event_create(event)
                    if transformed:
                        logger.info(f"✅ Transformation successful!")
                        logger.info(f"  Title: {transformed.title}")
                        logger.info(f"  Date: {transformed.date}")
                        logger.info(f"  Time: {transformed.time}")
                        logger.info(f"  Location: {transformed.location}")
                        logger.info(f"  Price: {transformed.price}")
                    else:
                        logger.warning(f"❌ Transformation failed - returned None")
                except Exception as e:
                    logger.error(f"❌ Transformation failed with error: {e}")
                
                logger.info("-" * 50)
        
        # Count successful transformations
        successful_transformations = 0
        failed_transformations = 0
        
        logger.info(f"\nProcessing all {len(raw_events)} events...")
        for i, event in enumerate(raw_events, 1):
            try:
                transformed = transformer.transform_to_event_create(event)
                if transformed:
                    successful_transformations += 1
                else:
                    failed_transformations += 1
                    if i <= 5:  # Show details for first few failures
                        logger.warning(f"Event {i} failed transformation. Raw data:")
                        logger.warning(f"  Title: {event.get('title', 'MISSING')}")
                        logger.warning(f"  Date: {event.get('date', 'MISSING')}")
                        logger.warning(f"  Link: {event.get('link', 'MISSING')}")
                        logger.warning(f"  Location: {event.get('location', 'MISSING')}")
            except Exception as e:
                failed_transformations += 1
                logger.error(f"Event {i} transformation error: {e}")
        
        logger.info(f"\nTransformation Summary:")
        logger.info(f"  ✅ Successful: {successful_transformations}")
        logger.info(f"  ❌ Failed: {failed_transformations}")
        logger.info(f"  📊 Success Rate: {successful_transformations/len(raw_events)*100:.1f}%")
        
        return successful_transformations > 0
        
    except Exception as e:
        logger.error(f"❌ Debug failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """Main debug function."""
    logger.info("🚀 Starting Croatia Scraper Transformation Debug")
    logger.info("=" * 60)
    
    success = await debug_transformation()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 Debug completed - found transformation issues!")
    else:
        logger.error("❌ Debug failed!")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Debug interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)