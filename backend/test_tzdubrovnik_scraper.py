#!/usr/bin/env python3
"""Test script for the improved tzdubrovnik scraper."""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.scraping.tzdubrovnik_scraper import scrape_tzdubrovnik_events


async def test_scraper():
    """Test the tzdubrovnik scraper functionality."""
    print("Testing Visit Dubrovnik scraper...")
    print("=" * 50)
    
    try:
        # Test with 2 months ahead to keep it reasonable for testing
        result = await scrape_tzdubrovnik_events(months_ahead=2)
        
        print(f"Status: {result['status']}")
        print(f"Message: {result['message']}")
        
        if result['status'] == 'success':
            print(f"Scraped events: {result['scraped_events']}")
            print(f"Saved events: {result['saved_events']}")
        
    except Exception as e:
        print(f"Error testing scraper: {e}")
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(test_scraper())
    if not success:
        sys.exit(1)
    print("Test completed successfully!")