#!/usr/bin/env python3
"""
Debug script to test the transformation of scraped data
"""
import asyncio
from app.scraping.entrio_scraper import EntrioScraper

async def debug_transformation():
    scraper = EntrioScraper()
    
    # Scrape raw events
    events = await scraper.scrape_events(max_pages=1)
    
    print(f"Scraped {len(events)} events after transformation")
    
    # Let's also get the raw data directly
    raw_events = await scraper.playwright_scraper.scrape_with_playwright(max_pages=1)
    print(f"Raw events: {len(raw_events)}")
    
    # Show first few raw events
    for i, raw_event in enumerate(raw_events[:3]):
        print(f"\nRaw Event {i+1}:")
        print(f"  Title: {raw_event.get('title', 'N/A')}")
        print(f"  Link: {raw_event.get('link', 'N/A')}")
        print(f"  Date: {raw_event.get('date', 'N/A')}")
        print(f"  Venue: {raw_event.get('venue', 'N/A')}")
        
        # Try transformation
        transformed = scraper.transformer.transform_to_event_create(raw_event)
        if transformed:
            print(f"  ✓ Transformation successful")
            print(f"    Name: {transformed.name}")
            print(f"    Date: {transformed.date}")
            print(f"    Location: {transformed.location}")
        else:
            print(f"  ✗ Transformation failed")

if __name__ == "__main__":
    asyncio.run(debug_transformation())