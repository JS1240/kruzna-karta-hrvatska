#!/usr/bin/env python3
"""
Test comprehensive geocoding on all Croatia events with the new enhanced system.
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


async def test_comprehensive_geocoding():
    """Test enhanced geocoding on all Croatia events."""
    logger.info("🗺️ Testing comprehensive geocoding on Croatia events...")
    
    try:
        db = SessionLocal()
        
        # Get all Croatia events without coordinates
        events_without_coords = db.query(Event).filter(
            Event.source == "croatia",
            Event.latitude.is_(None)
        ).all()
        
        logger.info(f"Found {len(events_without_coords)} Croatia events without coordinates")
        
        if not events_without_coords:
            logger.info("✅ All Croatia events already have coordinates!")
            return True
        
        # Show current location distribution
        location_counts = {}
        for event in events_without_coords:
            location = event.location
            location_counts[location] = location_counts.get(location, 0) + 1
        
        logger.info("Current location distribution:")
        for location, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  • {location}: {count} events")
        
        # Prepare locations for geocoding (limit to 10 for testing)
        test_events = events_without_coords[:10]
        locations_to_geocode = [(event.location, "Croatia") for event in test_events]
        
        logger.info(f"Testing geocoding on {len(locations_to_geocode)} sample locations...")
        
        # Use the enhanced geocoding system
        geocoding_results = await geocoding_service.batch_geocode_venues(locations_to_geocode)
        geocoded_count = len(geocoding_results)
        
        logger.info(f"Successfully geocoded {geocoded_count}/{len(locations_to_geocode)} locations")
        
        # Show geocoding results
        logger.info("Geocoding results:")
        for location, result in geocoding_results.items():
            logger.info(f"  • {location}: {result.latitude:.4f}, {result.longitude:.4f}")
            logger.info(f"    Source: {result.source}, Confidence: {result.confidence:.2f}, Accuracy: {result.accuracy}")
            logger.info(f"    Place: {result.place_name}")
        
        # Update sample events with coordinates
        updated_count = 0
        for event in test_events:
            if event.location in geocoding_results:
                result = geocoding_results[event.location]
                event.latitude = result.latitude
                event.longitude = result.longitude
                updated_count += 1
                logger.info(f"Updated coordinates for: {event.title}")
        
        # Commit the changes
        if updated_count > 0:
            db.commit()
            logger.info(f"✅ Updated {updated_count} events with coordinates")
        
        # Final statistics
        total_events = db.query(Event).filter(Event.source == "croatia").count()
        geocoded_events = db.query(Event).filter(
            Event.source == "croatia",
            Event.latitude.isnot(None)
        ).count()
        
        success_rate = (geocoded_events / total_events) * 100 if total_events > 0 else 0
        
        logger.info(f"Final geocoding statistics:")
        logger.info(f"  • Total Croatia events: {total_events}")
        logger.info(f"  • Geocoded events: {geocoded_events}")
        logger.info(f"  • Success rate: {success_rate:.1f}%")
        
        return geocoded_count > 0
        
    except Exception as e:
        logger.error(f"❌ Comprehensive geocoding test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False
    finally:
        db.close()


async def main():
    """Main test function."""
    logger.info("🚀 Testing Comprehensive Geocoding System")
    logger.info("=" * 60)
    
    success = await test_comprehensive_geocoding()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 Comprehensive geocoding test completed!")
    else:
        logger.error("❌ Comprehensive geocoding test failed!")
    
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