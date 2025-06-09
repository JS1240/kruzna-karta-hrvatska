#!/usr/bin/env python3
"""
Test script for Croatia.hr scraper to verify data quality and extraction.
"""

import asyncio
import sys
import os
import json
from datetime import datetime
import pytest

# Add the parent directory to the path to import our app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))



from app.scraping.croatia_scraper import CroatiaScraper


@pytest.mark.asyncio
async def test_croatia_scraper():
    """Test the Croatia.hr scraper and verify data quality."""
    print("=" * 60)
    print("Croatia.hr Scraper Test")
    print("=" * 60)
    
    scraper = CroatiaScraper()
    
    try:
        print("Starting Croatia.hr scraper test (max 1 page)...")
        print(f"Target URL: https://croatia.hr/hr-hr/dogadanja")
        print("-" * 60)
        
        # Test with just 1 page for quick verification
        events = await scraper.scrape_events(max_pages=1)
        
        print(f"\n✅ Scraping completed!")
        print(f"📊 Found {len(events)} valid events")
        
        if events:
            print("\n" + "=" * 40)
            print("SAMPLE EVENTS DATA")
            print("=" * 40)
            
            # Show first 3 events with detailed info
            for i, event in enumerate(events[:3], 1):
                print(f"\n📅 Event {i}:")
                print(f"   Name: {event.name}")
                print(f"   Date: {event.date}")
                print(f"   Time: {event.time}")
                print(f"   Location: {event.location}")
                print(f"   Price: {event.price}")
                print(f"   Description: {event.description[:100]}..." if len(event.description) > 100 else f"   Description: {event.description}")
                print(f"   Image: {event.image}")
                print(f"   Link: {event.link}")
            
            if len(events) > 3:
                print(f"\n... and {len(events) - 3} more events")
            
            # Data quality analysis
            print("\n" + "=" * 40)
            print("DATA QUALITY ANALYSIS")
            print("=" * 40)
            
            stats = {
                "total_events": len(events),
                "events_with_names": sum(1 for e in events if e.name and len(e.name) > 3),
                "events_with_dates": sum(1 for e in events if e.date),
                "events_with_locations": sum(1 for e in events if e.location and e.location != "Croatia"),
                "events_with_descriptions": sum(1 for e in events if e.description and len(e.description) > 20),
                "events_with_images": sum(1 for e in events if e.image),
                "events_with_links": sum(1 for e in events if e.link),
                "events_with_prices": sum(1 for e in events if e.price and e.price not in ["Check website", "Contact organizer"])
            }
            
            for key, value in stats.items():
                percentage = (value / stats["total_events"] * 100) if stats["total_events"] > 0 else 0
                print(f"   {key.replace('_', ' ').title()}: {value}/{stats['total_events']} ({percentage:.1f}%)")
            
            # Save test results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"croatia_scraper_test_{timestamp}.json"
            
            test_results = {
                "timestamp": timestamp,
                "scraper": "Croatia.hr",
                "url": "https://croatia.hr/hr-hr/dogadanja",
                "stats": stats,
                "sample_events": [
                    {
                        "name": event.name,
                        "date": str(event.date),
                        "time": event.time,
                        "location": event.location,
                        "description": event.description[:200] + "..." if len(event.description) > 200 else event.description,
                        "price": event.price,
                        "has_image": bool(event.image),
                        "has_link": bool(event.link)
                    }
                    for event in events[:5]  # Save first 5 events as samples
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(test_results, f, ensure_ascii=False, indent=2)
            
            print(f"\n💾 Test results saved to: {filename}")
            
            # Recommendations
            print("\n" + "=" * 40)
            print("RECOMMENDATIONS")
            print("=" * 40)
            
            if stats["events_with_names"] / stats["total_events"] < 0.8:
                print("⚠️  Consider improving title extraction selectors")
            
            if stats["events_with_dates"] / stats["total_events"] < 0.7:
                print("⚠️  Consider improving date extraction and parsing")
            
            if stats["events_with_locations"] / stats["total_events"] < 0.5:
                print("⚠️  Consider improving location extraction")
            
            if stats["events_with_images"] / stats["total_events"] < 0.3:
                print("⚠️  Consider improving image URL extraction")
            
            if stats["events_with_links"] / stats["total_events"] < 0.8:
                print("⚠️  Consider improving event link extraction")
            
            if all(ratio > 0.7 for ratio in [
                stats["events_with_names"] / stats["total_events"],
                stats["events_with_dates"] / stats["total_events"],
                stats["events_with_locations"] / stats["total_events"]
            ]):
                print("✅ Scraper quality looks good! Core fields are well extracted.")
        
        else:
            print("❌ No events found. This could indicate:")
            print("   - Website structure has changed")
            print("   - Events page is currently empty")
            print("   - Selectors need adjustment")
            print("   - JavaScript content not loading properly")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    return len(events) > 0 if 'events' in locals() else False


if __name__ == "__main__":
    # Test if playwright is available
    try:
        from playwright.async_api import async_playwright
        print("✅ Playwright is available")
    except ImportError:
        print("❌ Playwright not installed. Install with: pip install playwright")
        print("   Then run: playwright install")
        sys.exit(1)
    
    # Run the test
    success = asyncio.run(test_croatia_scraper())
    sys.exit(0 if success else 1)