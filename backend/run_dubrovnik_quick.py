#!/usr/bin/env python3
"""Quick test of the Dubrovnik scraper."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.scraping.tzdubrovnik_scraper import scrape_tzdubrovnik_events


async def main():
    """Run the Dubrovnik scraper for a short test."""
    print("🔄 Quick test of Visit Dubrovnik scraper...")
    print("=" * 50)
    
    try:
        # Run scraper for just 2 months to test functionality
        print("📅 Testing with 2 months ahead...")
        result = await scrape_tzdubrovnik_events(months_ahead=2)
        
        print(f"✅ Status: {result['status']}")
        print(f"📝 Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"📊 Total events scraped: {result['scraped_events']}")
            print(f"💾 New events saved to database: {result['saved_events']}")
            return True
        else:
            print(f"❌ Scraping failed: {result.get('message', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"💥 Error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)