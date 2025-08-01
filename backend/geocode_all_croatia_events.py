#!/usr/bin/env python3
"""
Geocode ALL remaining Croatia events to ensure 100% map coverage.
"""

import asyncio
import logging
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


async def geocode_all_croatia_events():
    """Geocode ALL Croatia events to ensure complete map coverage."""
    logger.info("🗺️ Geocoding ALL Croatia events for complete map coverage...")
    
    try:
        db = SessionLocal()
        
        # Get ALL Croatia events without coordinates
        events_without_coords = db.query(Event).filter(
            Event.source == "croatia",
            Event.latitude.is_(None)
        ).all()
        
        logger.info(f"Found {len(events_without_coords)} Croatia events without coordinates")
        
        if not events_without_coords:
            logger.info("✅ All Croatia events already have coordinates!")
            return True
        
        # Prepare ALL locations for geocoding
        locations_to_geocode = [(event.location, "Croatia") for event in events_without_coords]
        
        logger.info(f"Geocoding {len(locations_to_geocode)} locations...")
        logger.info("This may take a few minutes due to rate limiting...")
        
        # Use the enhanced geocoding system on ALL events
        geocoding_results = await geocoding_service.batch_geocode_venues(locations_to_geocode)
        geocoded_count = len(geocoding_results)
        
        logger.info(f"Successfully geocoded {geocoded_count}/{len(locations_to_geocode)} locations")
        
        # Show geocoding sources breakdown
        sources = {}
        for result in geocoding_results.values():
            sources[result.source] = sources.get(result.source, 0) + 1
        
        logger.info("Geocoding sources breakdown:")
        for source, count in sources.items():
            logger.info(f"  • {source}: {count} locations")
        
        # Update ALL events with coordinates
        updated_count = 0
        for event in events_without_coords:
            if event.location in geocoding_results:
                result = geocoding_results[event.location]
                event.latitude = result.latitude
                event.longitude = result.longitude
                updated_count += 1
                logger.debug(f"Updated coordinates for: {event.title}")
        
        # Commit ALL changes
        if updated_count > 0:
            db.commit()
            logger.info(f"✅ Updated {updated_count} events with coordinates")
        
        # Final comprehensive statistics
        total_events = db.query(Event).filter(Event.source == "croatia").count()
        geocoded_events = db.query(Event).filter(
            Event.source == "croatia",
            Event.latitude.isnot(None)
        ).count()
        
        success_rate = (geocoded_events / total_events) * 100 if total_events > 0 else 0
        
        logger.info("=" * 60)
        logger.info("🎯 FINAL GEOCODING STATISTICS")
        logger.info("=" * 60)
        logger.info(f"  • Total Croatia events: {total_events}")
        logger.info(f"  • Successfully geocoded: {geocoded_events}")
        logger.info(f"  • Events without coordinates: {total_events - geocoded_events}")
        logger.info(f"  • Overall success rate: {success_rate:.1f}%")
        
        # Show remaining ungeocodable events (if any)
        remaining_events = db.query(Event).filter(
            Event.source == "croatia",
            Event.latitude.is_(None)
        ).all()
        
        if remaining_events:
            logger.warning(f"Remaining ungeocodable events ({len(remaining_events)}):")
            for event in remaining_events:
                logger.warning(f"  • {event.title} - Location: {event.location}")
        else:
            logger.info("🎉 ALL CROATIA EVENTS ARE NOW GEOCODED AND WILL APPEAR ON THE MAP!")
        
        return success_rate >= 90  # Consider success if we geocoded 90%+ of events
        
    except Exception as e:
        logger.error(f"❌ Complete geocoding failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()


async def main():
    """Main geocoding function."""
    logger.info("🚀 Complete Croatia Events Geocoding")
    logger.info("=" * 60)
    
    success = await geocode_all_croatia_events()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 Complete geocoding successful!")
    else:
        logger.error("❌ Complete geocoding needs attention!")
    
    return success


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Geocoding interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)