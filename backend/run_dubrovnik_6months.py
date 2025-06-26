#!/usr/bin/env python3
"""Production script to run Dubrovnik scraper for 6 months of events."""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Override the database URL to use localhost
os.environ['DATABASE_URL'] = 'postgresql://postgres:postgres@localhost:5432/kruzna_karta_hrvatska'

from app.scraping.tzdubrovnik_scraper import scrape_tzdubrovnik_events


async def main():
    """Run the Dubrovnik scraper for 6 months of events."""
    print("🔄 Starting Visit Dubrovnik 6-Month Event Collection")
    print("=" * 70)
    print("📅 Extracting events for the next 6 months")
    
    # Calculate the date range
    start_date = datetime.now()
    end_date = start_date + timedelta(days=180)  # Approximately 6 months
    
    print(f"📅 Date Range: {start_date.strftime('%B %Y')} - {end_date.strftime('%B %Y')}")
    print(f"🌐 Source: https://visitdubrovnik.hr/attractions/event-calendar/")
    print("🔌 Database: localhost PostgreSQL")
    print("=" * 70)
    
    try:
        # Run scraper for 6 months ahead
        print("🚀 Starting calendar navigation and event extraction...")
        result = await scrape_tzdubrovnik_events(months_ahead=6)
        
        print("\n" + "=" * 70)
        print("📊 SCRAPING RESULTS")
        print("=" * 70)
        
        print(f"✅ Status: {result['status']}")
        print(f"📝 Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"📊 Total events scraped: {result['scraped_events']}")
            print(f"💾 New events saved to database: {result['saved_events']}")
            
            if result['saved_events'] > 0:
                print(f"\n🎉 SUCCESS: Added {result['saved_events']} new events from Visit Dubrovnik!")
                print("📍 Events from Dubrovnik region including:")
                print("   • Dubrovnik city events")
                print("   • Korčula island activities") 
                print("   • Čilipi folklore performances")
                print("   • Regional festivals and concerts")
                print("   • Cultural and music events")
                print(f"\n🗓️ Coverage: June - November 2025 ({6} months)")
            else:
                print("ℹ️ No new events found - all events may already be in database")
                print("   This is normal for subsequent runs of the scraper")
            
            print(f"\n✨ Dubrovnik scraper execution completed successfully!")
            return True
        else:
            print(f"❌ Scraping failed: {result.get('message', 'Unknown error')}")
            return False
        
    except Exception as e:
        print(f"\n💥 Error running scraper: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🇭🇷 Croatian Events Platform - Dubrovnik Event Scraper")
    print("🎯 Target: 6 months of comprehensive event coverage\n")
    
    success = asyncio.run(main())
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 SUCCESS: Dubrovnik events successfully collected and stored!")
        print("💡 Events are now available in the Croatian Events Platform")
    else:
        print("❌ FAILED: Please check the error messages above")
    
    print("=" * 70)
    sys.exit(0 if success else 1)