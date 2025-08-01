#!/usr/bin/env python3
"""
Update existing Croatia events with better location data extracted from URLs.
"""

import re
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.append(str(backend_dir))

from app.core.database import SessionLocal
from app.models.event import Event

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_location_from_url(url: str) -> str:
    """Extract location from Croatia.hr URL patterns."""
    if not url:
        return "Croatia"
    
    # Try to extract city/region from URL patterns
    url_match = re.search(r"visit([^.]+)\.croatia\.hr", url)
    if url_match:
        city_from_url = url_match.group(1).replace("-", " ").title()
        # Clean up common URL patterns
        city_from_url = city_from_url.replace("Central ", "Central-")  # "Central Istria"
        return city_from_url
    else:
        # Try other URL patterns
        domain_match = re.search(r"//([^/]+)\.croatia\.hr", url)
        if domain_match:
            domain_part = domain_match.group(1)
            if domain_part != "www" and domain_part != "croatia":
                return domain_part.replace("-", " ").title()
    
    return "Croatia"


def update_croatia_locations():
    """Update Croatia events with better location data from URLs."""
    logger.info("🗺️ Updating Croatia events with better location data...")
    
    try:
        db = SessionLocal()
        
        # Get all Croatia events with generic "Croatia" location
        events_to_update = db.query(Event).filter(
            Event.source == "croatia",
            Event.location == "Croatia"
        ).all()
        
        logger.info(f"Found {len(events_to_update)} Croatia events with generic location")
        
        updated_count = 0
        for event in events_to_update:
            if event.link:
                new_location = extract_location_from_url(event.link)
                if new_location != "Croatia" and new_location != event.location:
                    old_location = event.location
                    event.location = new_location
                    updated_count += 1
                    logger.info(f"Updated {event.title}: {old_location} → {new_location}")
        
        # Commit the changes
        if updated_count > 0:
            db.commit()
            logger.info(f"✅ Updated {updated_count} events with better location data")
        else:
            logger.info("No events needed location updates")
        
        # Show sample of updated events
        if updated_count > 0:
            updated_events = db.query(Event).filter(
                Event.source == "croatia",
                Event.location != "Croatia"
            ).limit(5).all()
            
            logger.info("Sample updated events:")
            for event in updated_events:
                logger.info(f"  • {event.title} - {event.location}")
        
        return updated_count
        
    except Exception as e:
        logger.error(f"❌ Failed to update Croatia locations: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main update function."""
    logger.info("🚀 Starting Croatia Location Update")
    logger.info("=" * 50)
    
    try:
        updated_count = update_croatia_locations()
        
        logger.info("=" * 50)
        logger.info(f"🎉 Location update completed! Updated {updated_count} events.")
        return True
        
    except Exception as e:
        logger.error(f"❌ Update failed: {e}")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Update interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)