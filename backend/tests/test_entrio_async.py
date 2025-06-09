import os
import sys

import pytest
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test")
from app.scraping.entrio_scraper import EntrioRequestsScraper


@pytest.mark.asyncio
async def test_scrape_events_page_async(monkeypatch):
    html = """
    <html><body>
        <div class="event-item">
            <a href="/event/1" class="event-link">
                <img src="img1.jpg" />
                <div class="event-title">Test Event 1</div>
            </a>
            <div class="event-date">01.01.2025</div>
            <div class="event-venue">Zagreb</div>
            <div class="price">100kn</div>
        </div>
        <a class="next" href="page2.html">Next</a>
    </body></html>
    """

    scraper = EntrioRequestsScraper()

    async def fake_fetch(url: str):
        return httpx.Response(status_code=200, text=html)

    monkeypatch.setattr(scraper, "fetch", fake_fetch)

    events, next_url = await scraper.scrape_events_page("http://test/page1")

    assert next_url.endswith("page2.html")
    assert len(events) == 1
    assert events[0]["title"] == "Test Event 1"


@pytest.mark.asyncio
async def test_scrape_all_events_async(monkeypatch):
    page1 = """
    <html><body>
        <div class="event-item">
            <a href="/event/1" class="event-link">
                <div class="event-title">Event 1</div>
            </a>
            <div class="event-date">01.01.2025</div>
        </div>
        <a class="next" href="page2.html">Next</a>
    </body></html>
    """

    page2 = """
    <html><body>
        <div class="event-item">
            <a href="/event/2" class="event-link">
                <div class="event-title">Event 2</div>
            </a>
            <div class="event-date">02.01.2025</div>
        </div>
    </body></html>
    """

    responses = {
        "http://test/page1": page1,
        "http://test/page2.html": page2,
    }

    scraper = EntrioRequestsScraper()

    async def fake_fetch(url: str):
        return httpx.Response(status_code=200, text=responses[url])

    monkeypatch.setattr(scraper, "fetch", fake_fetch)

    events = await scraper.scrape_all_events(start_url="http://test/page1", max_pages=2)

    titles = [e["title"] for e in events]
    assert titles == ["Event 1", "Event 2"]
    assert len(events) == 2
