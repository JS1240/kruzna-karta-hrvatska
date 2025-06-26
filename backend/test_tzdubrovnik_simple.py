#!/usr/bin/env python3
"""Simple test script for the improved tzdubrovnik scraper."""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

def test_imports():
    """Test that the scraper can be imported successfully."""
    try:
        from app.scraping.tzdubrovnik_scraper import (
            DubrovnikScraper, 
            DubrovnikTransformer,
            DubrovnikPlaywrightScraper,
            DubrovnikRequestsScraper,
            scrape_tzdubrovnik_events
        )
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False

def test_transformer():
    """Test the transformer with sample data."""
    try:
        from app.scraping.tzdubrovnik_scraper import DubrovnikTransformer
        
        # Test date parsing
        transformer = DubrovnikTransformer()
        
        # Test the new date format
        test_date = transformer.parse_date("24. June, 2025")
        if test_date and test_date.day == 24 and test_date.month == 6 and test_date.year == 2025:
            print("✓ Date parsing for '24. June, 2025' works correctly")
        else:
            print(f"✗ Date parsing failed, got: {test_date}")
            return False
        
        # Test event transformation
        sample_data = {
            "title": "Midsummer Scene Festival",
            "date": "24. June, 2025",
            "location": "Dubrovnik",
            "description": "Date: 24.06.2025<br>Location: Dubrovnik",
            "link": "https://visitdubrovnik.hr/events/midsummer-scene-6/",
            "image": "https://visitdubrovnik.hr/wp-content/uploads/2025/06/The-School-for-Scandal-2025-1.jpg"
        }
        
        event = transformer.transform(sample_data)
        if event and event.title == "Midsummer Scene Festival":
            print("✓ Event transformation works correctly")
        else:
            print(f"✗ Event transformation failed, got: {event}")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Transformer test error: {e}")
        return False

def test_scraper_initialization():
    """Test that the scraper can be initialized."""
    try:
        from app.scraping.tzdubrovnik_scraper import DubrovnikScraper
        
        scraper = DubrovnikScraper()
        if scraper.requests_scraper and scraper.playwright_scraper and scraper.transformer:
            print("✓ Scraper initialization successful")
            return True
        else:
            print("✗ Scraper initialization failed - missing components")
            return False
    except Exception as e:
        print(f"✗ Scraper initialization error: {e}")
        return False

if __name__ == "__main__":
    print("Testing Visit Dubrovnik scraper components...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_transformer,
        test_scraper_initialization
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The scraper is ready for use.")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the errors above.")
        sys.exit(1)