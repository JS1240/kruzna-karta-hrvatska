#!/usr/bin/env python3
"""
Test geocoding on existing Croatia events without coordinates.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.core.database import SessionLocal
from app.core.geocoding_service import geocoding_service
from app.models.event import Event

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_retroactive_geocoding():
    """Test geocoding on existing Croatia events."""
    logger.info("🗺️ Testing retroactive geocoding on existing Croatia events...")
    
    # Check if Mapbox token is available
    mapbox_token = os.getenv("VITE_MAPBOX_ACCESS_TOKEN")
    if not mapbox_token:
        logger.warning("⚠️ VITE_MAPBOX_ACCESS_TOKEN not set, geocoding will be skipped")
        return True  # Don't fail the test, just skip geocoding
    
    try:
        db = SessionLocal()
        
        # Get Croatia events without coordinates
        events_without_coords = db.query(Event).filter(
            Event.source == "croatia",
            Event.latitude.is_(None)
        ).limit(5).all()  # Limit to 5 for testing
        
        logger.info(f"Found {len(events_without_coords)} Croatia events without coordinates")
        
        if not events_without_coords:
            logger.info("✅ All Croatia events already have coordinates!")
            return True
        
        # Show sample events
        for i, event in enumerate(events_without_coords[:3], 1):
            logger.info(f"  {i}. {event.title} - Location: {event.location}")
        
        # Prepare locations for geocoding
        locations_to_geocode = [(event.location, "") for event in events_without_coords if event.location]
        logger.info(f"Geocoding {len(locations_to_geocode)} locations...")
        
        # Geocode the locations
        geocoding_results = await geocoding_service.batch_geocode_venues(locations_to_geocode)
        geocoded_count = len(geocoding_results)
        
        logger.info(f"Successfully geocoded {geocoded_count}/{len(locations_to_geocode)} locations")
        
        # Update events with coordinates
        updated_count = 0
        for event in events_without_coords:
            if event.location in geocoding_results:
                result = geocoding_results[event.location]
                event.latitude = result.latitude
                event.longitude = result.longitude
                updated_count += 1
                logger.info(f"Updated {event.title}: {result.latitude}, {result.longitude}")
        
        # Commit the changes
        db.commit()
        logger.info(f"✅ Updated {updated_count} events with coordinates")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Retroactive geocoding failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()


async def main():
    """Main test function."""
    logger.info("🚀 Testing Retroactive Geocoding")
    logger.info("=" * 50)
    
    success = await test_retroactive_geocoding()
    
    logger.info("=" * 50)
    if success:
        logger.info("🎉 Retroactive geocoding test completed!")
    else:
        logger.error("❌ Retroactive geocoding test failed!")
    
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