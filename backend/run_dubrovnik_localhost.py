#!/usr/bin/env python3
"""Run Dubrovnik scraper with localhost database connection."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Override the database URL to use localhost
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/kruzna_karta_hrvatska'

from app.scraping.tzdubrovnik_scraper import scrape_tzdubrovnik_events


async def main():
    """Run the Dubrovnik scraper and store events."""
    print("🔄 Starting Visit Dubrovnik event scraper...")
    print("🔌 Using localhost database connection")
    print("=" * 60)
    
    try:
        # Run scraper for 6 months ahead to get a comprehensive collection
        result = await scrape_tzdubrovnik_events(months_ahead=6)
        
        print(f"✅ Status: {result['status']}")
        print(f"📝 Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"📊 Total events scraped: {result['scraped_events']}")
            print(f"💾 New events saved to database: {result['saved_events']}")
            
            if result['saved_events'] > 0:
                print(f"🎉 Successfully added {result['saved_events']} new events from Visit Dubrovnik!")
                print("📍 Events include dates from Dubrovnik's interactive calendar")
                print("🗓️ Calendar dates from June, July, August, September, October, November 2025")
            else:
                print("ℹ️ No new events found (all events may already be in database)")
            
            return True
        else:
            print(f"❌ Scraping failed: {result.get('message', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"💥 Error running scraper: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("=" * 60)
    print("✨ Dubrovnik scraper execution completed!")


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'🎉 SUCCESS - Events stored in database!' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)