#!/usr/bin/env python3
"""Test script for InfoZagreb.hr scraper."""

import asyncio
import sys
import os
import json
from datetime import datetime
import pytest

# Add parent directory to import app modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.scraping.infozagreb_scraper import InfoZagrebScraper


@pytest.mark.asyncio
async def test_infozagreb_scraper():
    """Basic test for the InfoZagreb scraper."""
    print("=" * 60)
    print("InfoZagreb.hr Scraper Test")
    print("=" * 60)

    scraper = InfoZagrebScraper()

    try:
        print("Starting InfoZagreb scraper test (max 1 page)...")
        events = await scraper.scrape_events(max_pages=1)
        print(f"\n✅ Scraping completed: {len(events)} events")

        assert isinstance(events, list)

        if events:
            first = events[0]
            print("Sample event:")
            print(f"  Name: {first.name}")
            print(f"  Date: {first.date}")
            print(f"  Location: {first.location}")
            print(f"  Link: {first.link}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"infozagreb_scraper_test_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([e.model_dump() for e in events[:5]], f, ensure_ascii=False, indent=2)
        print(f"\nSaved sample data to {filename}")
    except Exception as e:
        print(f"Scraper failed: {e}")
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_infozagreb_scraper())
    sys.exit(0 if success else 1)
