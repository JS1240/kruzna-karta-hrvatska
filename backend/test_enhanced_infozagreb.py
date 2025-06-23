#!/usr/bin/env python3
"""
Test script for the enhanced InfoZagreb scraper.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.scraping.infozagreb_scraper import scrape_infozagreb_events, InfoZagrebScraper

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_enhanced_scraper():
    """Test the enhanced InfoZagreb scraper."""
    print("=== Testing Enhanced InfoZagreb Scraper ===\n")
    
    # Test 1: Multi-strategy scraping
    print("1. Testing multi-strategy scraping...")
    try:
        result = await scrape_infozagreb_events(max_pages=3, use_fallbacks=True)
        print(f"Result: {result}")
        print(f"Status: {result['status']}")
        print(f"Events found: {result['scraped_events']}")
        print(f"Events saved: {result['saved_events']}")
        print()
    except Exception as e:
        print(f"Multi-strategy test failed: {e}\n")
    
    # Test 2: Individual strategy testing
    print("2. Testing individual strategies...")
    scraper = InfoZagrebScraper()
    
    try:
        # Test API discovery
        print("   Testing API discovery...")
        api_events = await scraper.try_api_endpoints()
        print(f"   API events found: {len(api_events)}")
        
        # Test browser automation (if available)
        print("   Testing browser automation...")
        try:
            browser_events = await scraper.scrape_with_browser(max_pages=2)
            print(f"   Browser events found: {len(browser_events)}")
        except Exception as e:
            print(f"   Browser automation failed: {e}")
        
        # Test static scraping
        print("   Testing static scraping...")
        static_events = await scraper.scrape_all_events(max_pages=2)
        print(f"   Static events found: {len(static_events)}")
        
    except Exception as e:
        print(f"Individual strategy testing failed: {e}")
    finally:
        await scraper.close_browser()
    
    print("\n=== Test completed ===")

async def test_date_parsing():
    """Test the enhanced date parsing."""
    print("=== Testing Enhanced Date Parsing ===\n")
    
    scraper = InfoZagrebScraper()
    
    test_dates = [
        "15.12.2024",           # Croatian format
        "2024-12-15",           # ISO format
        "15 prosinca 2024",     # Croatian month name
        "15 December 2024",     # English month name
        "15.12.",               # Short format (current year)
        "15/12/2024",           # Alternative format
    ]
    
    for date_str in test_dates:
        parsed = scraper.parse_infozagreb_date(date_str)
        print(f"'{date_str}' -> {parsed}")
    
    print()

async def test_location_extraction():
    """Test Zagreb-specific location extraction."""
    print("=== Testing Location Extraction ===\n")
    
    scraper = InfoZagrebScraper()
    
    test_cases = [
        ("Concert at Lisinski", "Great concert hall", ""),
        ("Event at HNK", "Croatian National Theatre", ""),
        ("Meeting", "Business event", "Ilica 5"),
        ("Festival", "Music festival", ""),
    ]
    
    for title, description, base_location in test_cases:
        location = scraper._enhance_zagreb_location(base_location, title, description)
        print(f"Title: '{title}', Desc: '{description}', Base: '{base_location}' -> '{location}'")
    
    print()

if __name__ == "__main__":
    async def main():
        await test_date_parsing()
        await test_location_extraction()
        await test_enhanced_scraper()
    
    asyncio.run(main())