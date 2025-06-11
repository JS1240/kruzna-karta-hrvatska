#!/usr/bin/env python3
"""Test script for Zadar.travel scraper."""

import asyncio
import sys
import os
import json
from datetime import datetime
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.scraping.zadar_scraper import ZadarScraper


@pytest.mark.asyncio
async def test_zadar_scraper():
    """Basic test for the Zadar scraper."""
    scraper = ZadarScraper()
    try:
        events = await scraper.scrape_events(max_pages=1)
        assert isinstance(events, list)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"zadar_scraper_test_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump([e.model_dump() for e in events[:5]], f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Scraper failed: {e}")
        return False
    return True


if __name__ == "__main__":
    success = asyncio.run(test_zadar_scraper())
    sys.exit(0 if success else 1)
