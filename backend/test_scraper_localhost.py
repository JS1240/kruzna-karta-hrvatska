#!/usr/bin/env python3
"""
Test Croatia scraper with localhost database connection.
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
from app.models.event import Event
from app.models.schemas import EventCreate
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create database session with localhost
DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/kruzna_karta_hrvatska"
engine = create_engine(DATABASE_URL)
LocalSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def test_scraper_with_localhost():
    """Test Croatia scraper with localhost database."""
    logger.info("🕷️ Testing Croatia scraper with localhost database...")
    
    # Get environment variables
    user = os.getenv("BRIGHTDATA_USER", "demo_user")
    password = os.getenv("BRIGHTDATA_PASSWORD", "demo_password")
    port = os.getenv("BRIGHTDATA_PORT", "9222")
    use_scraping_browser = os.getenv("USE_SCRAPING_BROWSER", "")
    
    logger.info(f"Using Bright Data configuration:")
    logger.info(f"  • User: {user}")
    logger.info(f"  • Password: {'*' * len(password) if password != 'demo_password' else password}")
    logger.info(f"  • Port: {port}")
    logger.info(f"  • Scraping Browser URL: {'Set' if use_scraping_browser else 'Not set'}")
    
    try:
        # Test database connection first
        logger.info("Testing database connection...")
        db = LocalSession()
        initial_count = db.query(Event).filter(Event.source == "croatia").count()
        total_events = db.query(Event).count()
        logger.info(f"✅ Database connected - Total events: {total_events}, Croatia events: {initial_count}")
        db.close()
        
        # Manually patch the scraper configuration
        import app.scraping.croatia_scraper as scraper_module
        
        # Update the module-level variables
        scraper_module.USER = user
        scraper_module.PASSWORD = password
        scraper_module.BRIGHTDATA_PORT = int(port)
        scraper_module.PROXY = f"http://{user}:{password}@brd.superproxy.io:{port}"
        
        if use_scraping_browser:
            scraper_module.BRD_WSS = use_scraping_browser
        else:
            scraper_module.BRD_WSS = f"wss://{user}:{password}@brd.superproxy.io:9222"
        
        # Only use proxy if we have real credentials
        scraper_module.USE_PROXY = bool(user != "demo_user")
        
        logger.info(f"Scraper configuration:")
        logger.info(f"  • Use Proxy: {scraper_module.USE_PROXY}")
        logger.info(f"  • WebSocket: {scraper_module.BRD_WSS[:50]}...")
        
        # Create scraper instance
        class LocalCroatiaScraper(CroatiaScraper):
            def save_events_to_database(self, events) -> int:
                """Save events using localhost database session."""
                if not events:
                    return 0

                db = LocalSession()
                saved_count = 0

                try:
                    for event_data in events:
                        # Check if event already exists
                        existing = (
                            db.query(Event)
                            .filter(
                                Event.title == event_data.title, 
                                Event.date == event_data.date
                            )
                            .first()
                        )

                        if not existing:
                            db_event = Event(**event_data.model_dump())
                            db.add(db_event)
                            saved_count += 1
                            logger.info(f"Adding new event: {event_data.title}")
                        else:
                            logger.info(f"Event already exists: {event_data.title}")

                    db.commit()
                    logger.info(f"Saved {saved_count} new events to database")

                except Exception as e:
                    logger.error(f"Error saving events: {e}")
                    db.rollback()
                    raise
                finally:
                    db.close()

                return saved_count
        
        scraper = LocalCroatiaScraper()
        
        # Run scraper with very limited scope for testing
        logger.info("Running scraper (1 page, no details)...")
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
        
        # Save events to database
        saved_count = scraper.save_events_to_database(events)
        
        # Final count
        db = LocalSession()
        final_count = db.query(Event).filter(Event.source == "croatia").count()
        db.close()
        
        logger.info(f"✅ Test completed successfully!")
        logger.info(f"  • Scraped events: {len(events)}")
        logger.info(f"  • Saved events: {saved_count}")
        logger.info(f"  • Total Croatia events: {final_count}")
        
        return len(events) > 0
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


async def main():
    """Main test function."""
    logger.info("🚀 Starting Croatia Scraper Test with Localhost DB")
    logger.info("=" * 60)
    
    success = await test_scraper_with_localhost()
    
    logger.info("=" * 60)
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