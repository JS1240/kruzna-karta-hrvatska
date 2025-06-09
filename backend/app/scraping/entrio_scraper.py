"""
Entrio.hr event scraper integrated with the backend database.
Combines both BrightData proxy and Playwright approaches.
"""

import asyncio
import json
import os
import time
import re
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse, parse_qs
import httpx
from bs4 import BeautifulSoup, Tag
import pandas as pd
from sqlalchemy.orm import Session

from ..core.config import settings
from ..core.database import SessionLocal
from ..models.event import Event
from ..models.schemas import EventCreate

# BrightData configuration
USER = os.getenv("BRIGHTDATA_USER", "demo_user")
PASSWORD = os.getenv("BRIGHTDATA_PASSWORD", "demo_password")
BRIGHTDATA_HOST_RES = "brd.superproxy.io"
BRIGHTDATA_PORT = int(os.getenv("BRIGHTDATA_PORT", 22225))
SCRAPING_BROWSER_EP = f"https://brd.superproxy.io:{BRIGHTDATA_PORT}"
PROXY = f"http://{USER}:{PASSWORD}@{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"
BRD_WSS = f"wss://{USER}:{PASSWORD}@brd.superproxy.io:9222"

CATEGORY_URL = os.getenv("CATEGORY_URL", "https://www.entrio.hr/hr/")
USE_SB = os.getenv("USE_SCRAPING_BROWSER", "0") == "1"
USE_PROXY = os.getenv("USE_PROXY", "0") == "1"
USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT", "1") == "1"

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0"
}


class EventDataTransformer:
    """Transform scraped event data to database format."""

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Parse various date formats into Python date object."""
        if not date_str:
            return None

        # Common date patterns
        patterns = [
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})",  # DD.MM.YYYY
            r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
            r"(\d{1,2})/(\d{1,2})/(\d{4})",  # DD/MM/YYYY
            r"(\d{1,2})\s+(\w+)\s+(\d{4})",  # DD Month YYYY
        ]

        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    if "." in pattern or "/" in pattern:
                        day, month, year = match.groups()
                        return date(int(year), int(month), int(day))
                    elif "-" in pattern:
                        year, month, day = match.groups()
                        return date(int(year), int(month), int(day))
                    else:  # Month name format
                        day, month_name, year = match.groups()
                        # Croatian month names mapping
                        months = {
                            "siječnja": 1,
                            "veljače": 2,
                            "ožujka": 3,
                            "travnja": 4,
                            "svibnja": 5,
                            "lipnja": 6,
                            "srpnja": 7,
                            "kolovoza": 8,
                            "rujna": 9,
                            "listopada": 10,
                            "studenoga": 11,
                            "prosinca": 12,
                            "januar": 1,
                            "februar": 2,
                            "mart": 3,
                            "april": 4,
                            "maj": 5,
                            "jun": 6,
                            "jul": 7,
                            "avgust": 8,
                            "septembar": 9,
                            "oktobar": 10,
                            "novembar": 11,
                            "decembar": 12,
                        }
                        month_num = months.get(month_name.lower(), 1)
                        return date(int(year), month_num, int(day))
                except (ValueError, TypeError):
                    continue

        # Fallback: try to extract at least year
        year_match = re.search(r"(\d{4})", date_str)
        if year_match:
            try:
                return date(int(year_match.group(1)), 1, 1)
            except ValueError:
                pass

        return None

    @staticmethod
    def parse_time(time_str: str) -> str:
        """Parse time string and return in HH:MM format."""
        if not time_str:
            return "20:00"  # Default time

        # Look for time patterns
        time_match = re.search(r"(\d{1,2}):(\d{2})", time_str)
        if time_match:
            hour, minute = time_match.groups()
            return f"{int(hour):02d}:{minute}"

        # Look for hour only
        hour_match = re.search(r"(\d{1,2})h", time_str)
        if hour_match:
            hour = hour_match.group(1)
            return f"{int(hour):02d}:00"

        return "20:00"  # Default time

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        return " ".join(text.strip().split())

    @staticmethod
    def transform_to_event_create(scraped_data: Dict) -> Optional[EventCreate]:
        """Transform scraped data to EventCreate schema."""
        try:
            # Extract and clean basic fields
            name = EventDataTransformer.clean_text(scraped_data.get("title", ""))
            location = EventDataTransformer.clean_text(
                scraped_data.get("venue", "") or scraped_data.get("location", "")
            )
            description = EventDataTransformer.clean_text(
                scraped_data.get("description", "")
            )
            price = EventDataTransformer.clean_text(scraped_data.get("price", ""))

            # Parse date
            date_str = scraped_data.get("date", "")
            parsed_date = EventDataTransformer.parse_date(date_str)
            if not parsed_date:
                # Skip events without valid dates
                return None

            # Parse time
            time_str = scraped_data.get("time", "") or scraped_data.get("date", "")
            parsed_time = EventDataTransformer.parse_time(time_str)

            # Handle image URL
            image_url = scraped_data.get("image_url", "")
            if image_url and not image_url.startswith("http"):
                image_url = urljoin("https://entrio.hr", image_url)

            # Handle event link
            link = scraped_data.get("link", "")
            if link and not link.startswith("http"):
                link = urljoin("https://entrio.hr", link)

            # Validate required fields
            if not name or len(name) < 3:
                return None

            if not location:
                location = "Zagreb, Croatia"  # Default location

            return EventCreate(
                name=name,
                time=parsed_time,
                date=parsed_date,
                location=location,
                description=description or f"Event: {name}",
                price=price or "Contact organizer",
                image=image_url,
                link=link,
            )

        except Exception as e:
            print(f"Error transforming event data: {e}")
            return None


class EntrioRequestsScraper:
    """Scraper using httpx and BeautifulSoup."""

    def __init__(self):
        pass

    async def fetch(self, url: str) -> httpx.Response:
        """Fetch URL with proxy support."""
        try:
            async with httpx.AsyncClient() as client:
                if USE_SB and USE_PROXY:
                    params = {"url": url}
                    resp = await client.get(
                        SCRAPING_BROWSER_EP,
                        params=params,
                        headers=HEADERS,
                        auth=(USER, PASSWORD),
                        timeout=30,
                        verify=False,
                    )
                elif USE_PROXY:
                    resp = await client.get(
                        url,
                        headers=HEADERS,
                        proxies={"http://": PROXY, "https://": PROXY},
                        timeout=30,
                        verify=False,
                    )
                else:
                    resp = await client.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp
        except httpx.HTTPError as e:
            print(f"[ERROR] Request failed for {url}: {e}")
            raise

    def parse_event_from_element(self, event_element: Tag) -> Dict:
        """Extract event details from a single event element."""
        event_data = {}

        try:
            # Extract event link
            link_patterns = [
                "a.poster-image",
                'a[class*="event"]',
                'a[href*="/event/"]',
                'a[href*="/dogadaj/"]',
                "a",
            ]

            for pattern in link_patterns:
                link_element = event_element.select_one(pattern)
                if link_element and isinstance(link_element, Tag):
                    href = link_element.get("href")
                    if href and isinstance(href, str):
                        event_data["link"] = (
                            urljoin("https://entrio.hr", href)
                            if href.startswith("/")
                            else href
                        )
                        break

            # Extract image URL
            img_patterns = ["img[src]", "img[data-src]", '[style*="background-image"]']
            for pattern in img_patterns:
                img_element = event_element.select_one(pattern)
                if img_element and isinstance(img_element, Tag):
                    src = img_element.get("src") or img_element.get("data-src")
                    if src and isinstance(src, str):
                        event_data["image_url"] = src
                        break

            # Extract title
            title_patterns = [
                ".event-title",
                ".title",
                "h1, h2, h3, h4, h5, h6",
                '[class*="title"]',
                '[class*="name"]',
            ]
            for pattern in title_patterns:
                title_element = event_element.select_one(pattern)
                if title_element:
                    title_text = title_element.get_text(strip=True)
                    if title_text and len(title_text) > 2:
                        event_data["title"] = title_text
                        break

            # Extract date
            date_patterns = [
                ".date-overlay",
                ".date",
                ".event-date",
                '[class*="date"]',
                "time",
            ]
            for pattern in date_patterns:
                date_element = event_element.select_one(pattern)
                if date_element:
                    date_text = date_element.get_text(strip=True)
                    if date_text:
                        event_data["date"] = date_text
                        break

            # Extract venue/location
            venue_patterns = [
                ".event-venue",
                ".venue",
                ".location",
                '[class*="venue"]',
                '[class*="location"]',
            ]
            for pattern in venue_patterns:
                venue_element = event_element.select_one(pattern)
                if venue_element:
                    venue_text = venue_element.get_text(strip=True)
                    if venue_text:
                        event_data["venue"] = venue_text
                        break

            # Extract price
            price_patterns = [
                ".price",
                ".event-price",
                '[class*="price"]',
                '[class*="cost"]',
            ]
            for pattern in price_patterns:
                price_element = event_element.select_one(pattern)
                if price_element:
                    price_text = price_element.get_text(strip=True)
                    if price_text:
                        event_data["price"] = price_text
                        break

        except Exception as e:
            print(f"Error parsing event element: {e}")

        return event_data

    async def scrape_events_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        """Scrape events from a single page."""
        print(f"→ Fetching {url}")
        resp = await self.fetch(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        events = []

        # Event selectors
        event_selectors = [
            ".poster-image",
            ".event-poster",
            ".event-item",
            ".event-card",
            ".event-listing",
            '[class*="event"]',
            'article[class*="event"]',
            'div[class*="card"]',
            'a[href*="/event/"]',
            'a[href*="/dogadaj/"]',
        ]

        event_elements = []
        for selector in event_selectors:
            elements = soup.select(selector)
            if len(elements) > 0:
                print(f"Found {len(elements)} events using selector: {selector}")
                event_elements = elements
                break

        # Parse events
        for event_element in event_elements:
            if isinstance(event_element, Tag):
                event_data = self.parse_event_from_element(event_element)
                if event_data and len(event_data) > 1:
                    events.append(event_data)

        # Find next page
        next_page_url = None
        pagination_selectors = [
            'a[class*="next"]',
            'a[aria-label*="Next"]',
            ".pagination a:last-child",
            'a[rel="next"]',
        ]

        for selector in pagination_selectors:
            next_link = soup.select_one(selector)
            if next_link and isinstance(next_link, Tag):
                href = next_link.get("href")
                if href and isinstance(href, str):
                    next_page_url = urljoin(url, href)
                    break

        print(f"Extracted {len(events)} events from page")
        return events, next_page_url

    async def scrape_all_events(
        self, start_url: str = "https://entrio.hr/events", max_pages: int = 5
    ) -> List[Dict]:
        """Scrape all events with pagination."""
        all_events: List[Dict] = []
        to_visit: List[str] = [start_url]
        visited = 0

        concurrency = 3
        semaphore = asyncio.Semaphore(concurrency)

        async def worker(url: str) -> Tuple[List[Dict], Optional[str]]:
            async with semaphore:
                result = await self.scrape_events_page(url)
                await asyncio.sleep(1)
                return result

        while to_visit and visited < max_pages:
            batch = []
            while (
                to_visit
                and len(batch) < concurrency
                and visited + len(batch) < max_pages
            ):
                url = to_visit.pop(0)
                batch.append(worker(url))

            results = await asyncio.gather(*batch)

            for events, next_url in results:
                visited += 1
                all_events.extend(events)
                print(
                    f"Page {visited}: Found {len(events)} events (Total: {len(all_events)})"
                )
                if next_url and visited < max_pages:
                    to_visit.append(next_url)

        return all_events


class EntrioPlaywrightScraper:
    """Scraper using Playwright for JavaScript-heavy pages."""

    async def scrape_with_playwright(
        self, start_url: str = "https://entrio.hr/events", max_pages: int = 3
    ) -> List[Dict]:
        """Scrape events using Playwright."""
        from playwright.async_api import async_playwright

        all_events = []
        current_url = start_url
        page_count = 0

        async with async_playwright() as p:
            if USE_PROXY:
                browser = await p.chromium.connect_over_cdp(BRD_WSS)
            else:
                browser = await p.chromium.launch()

            page = await browser.new_page()

            while current_url and page_count < max_pages:
                try:
                    print(f"→ Fetching {current_url}")
                    await page.goto(
                        current_url, wait_until="domcontentloaded", timeout=90000
                    )

                    # Wait for content to load
                    await page.wait_for_timeout(3000)

                    # Extract events using JavaScript evaluation
                    events_data = await page.evaluate(
                        """
                        () => {
                            const events = [];
                            const eventSelectors = [
                                'a[href*="/event/"]:not([href*="/my_events"])',
                                'div[class*="event-card"]',
                                'div[class*="event-item"]',
                                'article[class*="event"]'
                            ];
                            
                            let eventElements = [];
                            for (const selector of eventSelectors) {
                                const elements = document.querySelectorAll(selector);
                                if (elements.length > 0) {
                                    eventElements = Array.from(elements);
                                    break;
                                }
                            }
                            
                            eventElements.forEach(element => {
                                const data = {};
                                
                                // Extract link
                                const linkEl = element.querySelector('a') || element;
                                if (linkEl && linkEl.href) {
                                    data.link = linkEl.href;
                                }
                                
                                // Extract title
                                const titleEl = element.querySelector('.event-title, .title, h1, h2, h3, h4, h5, h6');
                                if (titleEl) {
                                    data.title = titleEl.textContent.trim();
                                }
                                
                                // Extract date
                                const dateEl = element.querySelector('.date, .event-date, time');
                                if (dateEl) {
                                    data.date = dateEl.textContent.trim();
                                }
                                
                                // Extract venue
                                const venueEl = element.querySelector('.venue, .location, .event-venue');
                                if (venueEl) {
                                    data.venue = venueEl.textContent.trim();
                                }
                                
                                // Extract image
                                const imgEl = element.querySelector('img');
                                if (imgEl && imgEl.src) {
                                    data.image_url = imgEl.src;
                                }
                                
                                // Extract price
                                const priceEl = element.querySelector('.price, .event-price');
                                if (priceEl) {
                                    data.price = priceEl.textContent.trim();
                                }
                                
                                if (data.title || data.link) {
                                    events.push(data);
                                }
                            });
                            
                            return events;
                        }
                    """
                    )

                    all_events.extend(events_data)
                    page_count += 1
                    print(
                        f"Page {page_count}: Found {len(events_data)} events (Total: {len(all_events)})"
                    )

                    if not events_data:
                        break

                    # Try to find next page
                    next_link = await page.query_selector(
                        'a[class*="next"], a[aria-label*="Next"]'
                    )
                    if next_link:
                        current_url = await next_link.get_attribute("href")
                        if current_url:
                            current_url = urljoin(start_url, current_url)
                        else:
                            break
                    else:
                        break

                    await asyncio.sleep(2)

                except Exception as e:
                    print(f"Failed to scrape page {current_url}: {e}")
                    break

            await browser.close()

        return all_events


class EntrioScraper:
    """Main scraper class that combines both approaches."""

    def __init__(self):
        self.requests_scraper = EntrioRequestsScraper()
        self.playwright_scraper = EntrioPlaywrightScraper()
        self.transformer = EventDataTransformer()

    async def scrape_events(
        self, max_pages: int = 5, use_playwright: bool = None
    ) -> List[EventCreate]:
        """Scrape events and return as EventCreate objects."""
        if use_playwright is None:
            use_playwright = USE_PLAYWRIGHT

        print(f"Starting Entrio.hr scraper (Playwright: {use_playwright})")

        # Scrape raw data
        if use_playwright:
            raw_events = await self.playwright_scraper.scrape_with_playwright(
                max_pages=max_pages
            )
        else:
            raw_events = await self.requests_scraper.scrape_all_events(
                max_pages=max_pages
            )

        print(f"Scraped {len(raw_events)} raw events")

        # Transform to EventCreate objects
        events = []
        for raw_event in raw_events:
            event = self.transformer.transform_to_event_create(raw_event)
            if event:
                events.append(event)

        print(f"Transformed {len(events)} valid events")
        return events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        """Save events to database and return count of saved events."""
        if not events:
            return 0

        db = SessionLocal()
        saved_count = 0

        try:
            for event_data in events:
                # Check if event already exists (by name and date)
                existing = (
                    db.query(Event)
                    .filter(
                        Event.name == event_data.name, Event.date == event_data.date
                    )
                    .first()
                )

                if not existing:
                    db_event = Event(**event_data.model_dump())
                    db.add(db_event)
                    saved_count += 1
                else:
                    print(f"Event already exists: {event_data.name}")

            db.commit()
            print(f"Saved {saved_count} new events to database")

        except Exception as e:
            print(f"Error saving events to database: {e}")
            db.rollback()
            raise
        finally:
            db.close()

        return saved_count


# Convenience functions for API endpoints
async def scrape_entrio_events(max_pages: int = 5) -> Dict:
    """Scrape Entrio events and save to database."""
    scraper = EntrioScraper()

    try:
        events = await scraper.scrape_events(max_pages=max_pages)
        saved_count = scraper.save_events_to_database(events)

        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved_count,
            "message": f"Successfully scraped {len(events)} events, saved {saved_count} new events",
        }

    except Exception as e:
        return {"status": "error", "message": f"Scraping failed: {str(e)}"}
