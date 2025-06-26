#!/usr/bin/env python3
"""Script to run the Dubrovnik scraper and store events in the database."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.scraping.tzdubrovnik_scraper import scrape_tzdubrovnik_events


async def main():
    """Run the Dubrovnik scraper and store events."""
    print("🔄 Starting Visit Dubrovnik event scraper...")
    print("=" * 60)
    
    try:
        # Run scraper for 6 months ahead to get a good collection of events
        result = await scrape_tzdubrovnik_events(months_ahead=6)
        
        print(f"✅ Status: {result['status']}")
        print(f"📝 Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"📊 Total events scraped: {result['scraped_events']}")
            print(f"💾 New events saved to database: {result['saved_events']}")
            
            if result['saved_events'] > 0:
                print(f"🎉 Successfully added {result['saved_events']} new events from Visit Dubrovnik!")
            else:
                print("ℹ️ No new events found (all events may already be in database)")
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
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)