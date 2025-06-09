#!/usr/bin/env python3
"""
Database setup script for Kruzna Karta Hrvatska backend.
This script creates the database tables and inserts sample data.
"""

import os
import sys
import logging
from datetime import date

# Add the parent directory to the path to import our app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
logger = logging.getLogger(__name__)

from sqlalchemy import create_engine
from app.core.config import settings
from app.core.database import Base
from app.models.event import Event
from app.core.database import SessionLocal


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    engine = create_engine(settings.database_url)
    Base.metadata.create_all(bind=engine)
    logger.info("Tables created successfully!")


def insert_sample_data():
    """Insert sample events data."""
    logger.info("Inserting sample data...")
    
    db = SessionLocal()
    try:
        # Check if we already have data
        existing_events = db.query(Event).count()
        if existing_events > 0:
            logger.info(f"Database already contains {existing_events} events. Skipping sample data insertion.")
            return

        sample_events = [
            Event(
                name="Nina Badrić Concert",
                time="20:00",
                date=date(2025, 6, 15),
                location="Poljud Stadium, Split",
                description="Enjoy the wonderful voice of Nina Badrić in this special summer concert.",
                price="30-50€",
                image="/event-images/concert.jpg",
                link="https://entrio.hr/"
            ),
            Event(
                name="Zagreb Bootcamp Challenge",
                time="09:00",
                date=date(2025, 5, 20),
                location="Jarun Lake, Zagreb",
                description="Join us for an intensive workout session in the heart of Zagreb.",
                price="15€",
                image="/event-images/workout.jpg",
                link="https://meetup.com/"
            ),
            Event(
                name="Dubrovnik Tech Meetup",
                time="18:00",
                date=date(2025, 7, 10),
                location="Hotel Excelsior, Dubrovnik",
                description="Network with tech professionals and enthusiasts from the region.",
                price="Free",
                image="/event-images/meetup.jpg",
                link="https://meetup.com/"
            ),
            Event(
                name="Adriatic Business Conference",
                time="10:00",
                date=date(2025, 9, 5),
                location="Rijeka Convention Center, Rijeka",
                description="Annual conference focusing on business opportunities in the Adriatic region.",
                price="100-200€",
                image="/event-images/conference.jpg",
                link="https://eventim.hr/"
            ),
            Event(
                name="Zrće Beach Party",
                time="23:00",
                date=date(2025, 8, 1),
                location="Papaya Club, Novalja",
                description="The biggest summer party on the famous Zrće beach.",
                price="25-40€",
                image="/event-images/party.jpg",
                link="https://entrio.hr/"
            )
        ]

        for event in sample_events:
            db.add(event)
            logger.info(f"Added event: {event.name}")

        db.commit()
        logger.info("Sample data inserted successfully!")

    except Exception as e:
        logger.error(f"Error inserting sample data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main setup function."""
    logger.info("Setting up Kruzna Karta Hrvatska database...")
    logger.info(f"Database URL: {settings.database_url}")
    
    try:
        create_tables()
        insert_sample_data()
        logger.info("\n✅ Database setup completed successfully!")
        logger.info("\nYou can now start the backend server with:")
        logger.info("cd backend && uv run uvicorn app.main:app --reload")
        
    except Exception as e:
        logger.error(f"\n❌ Database setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()