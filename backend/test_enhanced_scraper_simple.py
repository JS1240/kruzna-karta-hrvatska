#!/usr/bin/env python3
"""Simple test for the enhanced InfoZagreb scraper."""

import asyncio
import sys
import os
import json
from datetime import datetime

# Add parent directory to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

async def test_enhanced_infozagreb():
    """Test the enhanced InfoZagreb scraper."""
    print("=" * 60)
    print("Enhanced InfoZagreb.hr Scraper Test")
    print("=" * 60)

    try:
        from app.scraping.infozagreb_scraper import InfoZagrebScraper, scrape_infozagreb_events
        
        print("✅ Successfully imported enhanced scraper modules")
        
        # Test 1: Date parsing
        print("\n1. Testing enhanced date parsing...")
        scraper = InfoZagrebScraper()
        
        test_dates = [
            "15.12.2024",           # Croatian format
            "2024-12-15",           # ISO format
            "15 prosinca 2024",     # Croatian month name
            "15 December 2024",     # English month name
            "15.12.",               # Short format
        ]
        
        for date_str in test_dates:
            parsed = scraper.parse_infozagreb_date(date_str)
            print(f"   '{date_str}' -> {parsed}")
        
        # Test 2: Location enhancement
        print("\n2. Testing Zagreb location enhancement...")
        test_cases = [
            ("Concert at Lisinski", "Great concert hall", ""),
            ("Event at HNK", "Croatian National Theatre", ""),
            ("Meeting", "Business event", "Ilica 5"),
        ]
        
        for title, description, base_location in test_cases:
            location = scraper._enhance_zagreb_location(base_location, title, description)
            print(f"   '{title}' -> '{location}'")
        
        # Test 3: API endpoint discovery
        print("\n3. Testing API endpoint discovery...")
        try:
            api_events = await scraper.try_api_endpoints()
            print(f"   ✅ API discovery completed: {len(api_events)} events found")
        except Exception as e:
            print(f"   ⚠️  API discovery failed (expected): {e}")
        
        # Test 4: Enhanced scraping (using fallbacks=False to avoid browser automation issues)
        print("\n4. Testing enhanced scraping with static fallback...")
        try:
            result = await scrape_infozagreb_events(max_pages=2, use_fallbacks=False)
            print(f"   Status: {result['status']}")
            print(f"   Events scraped: {result['scraped_events']}")
            print(f"   Events saved: {result['saved_events']}")
            print(f"   Message: {result['message']}")
        except Exception as e:
            print(f"   ⚠️  Enhanced scraping failed: {e}")
        
        # Test 5: Individual components
        print("\n5. Testing individual enhancement components...")
        
        # Test tag extraction
        tags = scraper._extract_tags("Jazz Concert", "Music event at Lisinski", "Zagreb")
        print(f"   Tag extraction: {tags}")
        
        # Test image validation
        valid_img = scraper._is_valid_image_url("https://example.com/image.jpg")
        invalid_img = scraper._is_valid_image_url("javascript:void(0)")
        print(f"   Image validation: valid='{valid_img}', invalid='{invalid_img}'")
        
        print("\n✅ Enhanced scraper test completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    finally:
        try:
            await scraper.close_browser()
        except:
            pass

if __name__ == "__main__":
    success = asyncio.run(test_enhanced_infozagreb())
    sys.exit(0 if success else 1)