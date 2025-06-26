#!/usr/bin/env python3
"""Simple Dubrovnik scraper test with 1 month only."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Override the database URL to use localhost
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/kruzna_karta_hrvatska'

from app.scraping.tzdubrovnik_scraper import scrape_tzdubrovnik_events


async def main():
    """Run the Dubrovnik scraper for 1 month only."""
    print("🔄 Testing Visit Dubrovnik scraper (1 month)...")
    print("=" * 50)
    
    try:
        # Run scraper for just 1 month to test quickly
        result = await scrape_tzdubrovnik_events(months_ahead=1)
        
        print(f"✅ Status: {result['status']}")
        print(f"📝 Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"📊 Events scraped: {result['scraped_events']}")
            print(f"💾 Events saved: {result['saved_events']}")
            return True
        else:
            print(f"❌ Error: {result.get('message', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"💥 Exception: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"Result: {'SUCCESS' if success else 'FAILED'}")
    sys.exit(0 if success else 1)