#!/usr/bin/env python3
"""Test script for the enhanced Zadar scraper."""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend.app.scraping.zadar_scraper import scrape_zadar_events

async def test_zadar_scraper():
    """Test the Zadar scraper with a small number of pages."""
    print("Testing enhanced Zadar scraper...")
    print("=" * 50)
    
    try:
        # Test with just 1 page first
        result = await scrape_zadar_events(max_pages=1)
        
        print("\nScraping Results:")
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        print(f"Scraped events: {result.get('scraped_events', 0)}")
        print(f"Saved events: {result.get('saved_events', 0)}")
        
        if result['status'] == 'success' and result.get('scraped_events', 0) > 0:
            print("\n✅ Zadar scraper is working correctly!")
        else:
            print(f"\n❌ Zadar scraper needs attention: {result}")
            
    except Exception as e:
        print(f"\n❌ Error testing Zadar scraper: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_zadar_scraper())