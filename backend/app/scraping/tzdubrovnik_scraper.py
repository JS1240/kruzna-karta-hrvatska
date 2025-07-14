"""Visit Dubrovnik events scraper with interactive calendar support."""

from __future__ import annotations

import asyncio
import os
import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from ..models.schemas import EventCreate

# Import configuration
from ..config.components import get_settings

# Get global configuration
_settings = get_settings()
_scraping_config = _settings.scraping

# BrightData configuration
USER = _scraping_config.brightdata_user
PASSWORD = _scraping_config.brightdata_password
BRIGHTDATA_HOST_RES = _scraping_config.brightdata_host
BRIGHTDATA_PORT = _scraping_config.brightdata_port
SCRAPING_BROWSER_EP = _scraping_config.scraping_browser_endpoint
PROXY = _scraping_config.proxy_url

USE_SB = _scraping_config.use_scraping_browser
USE_PROXY = _scraping_config.use_proxy

HEADERS = _scraping_config.headers_dict

BASE_URL = "https://visitdubrovnik.hr"
EVENTS_URL = f"{BASE_URL}/attractions/event-calendar/"



class DubrovnikTransformer:
    """Transform raw event data to :class:`EventCreate`."""

    MONTHS = {
        # Croatian months
        "siječanj": 1, "veljača": 2, "ožujak": 3, "travanj": 4,
        "svibanj": 5, "lipanj": 6, "srpanj": 7, "kolovoz": 8,
        "rujan": 9, "listopad": 10, "studeni": 11, "prosinac": 12,
        # English months
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
    }

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Parse date from various formats including '24. June, 2025'."""
        if not date_str:
            return None
        
        date_str = date_str.strip()
        
        # Handle "24. June, 2025" format
        pattern = r"(\d{1,2})\.\s*(\w+),?\s*(\d{4})"
        match = re.search(pattern, date_str, re.IGNORECASE)
        if match:
            try:
                day, month_name, year = match.groups()
                month_num = DubrovnikTransformer.MONTHS.get(month_name.lower())
                if month_num:
                    return date(int(year), month_num, int(day))
            except (ValueError, TypeError):
                pass
        
        # Handle standard formats
        patterns = [
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})",  # DD.MM.YYYY
            r"(\d{4})-(\d{1,2})-(\d{1,2})",   # YYYY-MM-DD
            r"(\d{1,2})\s+(\w+)\s+(\d{4})",   # DD Month YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if pattern.startswith(r"(\d{1,2})\."):
                        day, month, year = match.groups()
                        return date(int(year), int(month), int(day))
                    elif pattern.startswith(r"(\d{4})"):
                        year, month, day = match.groups()
                        return date(int(year), int(month), int(day))
                    else:  # Month name format
                        day, month_name, year = match.groups()
                        month_num = DubrovnikTransformer.MONTHS.get(month_name.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                except (ValueError, TypeError):
                    continue
        
        return None

    @staticmethod
    def parse_time(time_str: str) -> str:
        """Parse time from text, default to 20:00."""
        if not time_str:
            return "20:00"
        
        match = re.search(r"(\d{1,2}):(\d{2})", time_str)
        if match:
            hour, minute = match.groups()
            return f"{int(hour):02d}:{minute}"
        
        match = re.search(r"(\d{1,2})h", time_str)
        if match:
            hour = match.group(1)
            return f"{int(hour):02d}:00"
        
        return "20:00"

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        return " ".join(text.split()) if text else ""

    @classmethod
    def transform(cls, data: Dict) -> Optional[EventCreate]:
        """Transform raw event data to EventCreate object."""
        try:
            title = cls.clean_text(data.get("title", ""))
            location = cls.clean_text(data.get("location", "Dubrovnik"))
            description = cls.clean_text(data.get("description", ""))
            price = cls.clean_text(data.get("price", ""))

            # Try to parse date from the main date field first
            date_str = data.get("date", "")
            parsed_date = cls.parse_date(date_str)
            
            # If that fails, try to extract date from description
            if not parsed_date and description:
                # Look for "Date: DD.MM.YYYY" pattern in description
                desc_date_match = re.search(r"Date:\s*(\d{1,2})\.(\d{1,2})\.(\d{4})", description)
                if desc_date_match:
                    day, month, year = desc_date_match.groups()
                    try:
                        parsed_date = date(int(year), int(month), int(day))
                    except (ValueError, TypeError):
                        pass
            
            if not parsed_date:
                return None

            time_str = data.get("time", "")
            parsed_time = cls.parse_time(time_str)

            image = data.get("image")
            if image and not image.startswith("http"):
                image = urljoin(BASE_URL, image)

            link = data.get("link")
            if link and not link.startswith("http"):
                link = urljoin(BASE_URL, link)

            if not title or len(title) < 3:
                return None

            return EventCreate(
                title=title,
                time=parsed_time,
                date=parsed_date,
                location=location or "Dubrovnik",
                description=description or f"Event: {title}",
                price=price or "Check website",
                image=image,
                link=link,
                source="manual",
            )
        except Exception:
            return None


class DubrovnikRequestsScraper:
    """Fallback scraper using httpx and BeautifulSoup."""

    def __init__(self) -> None:
        if USE_PROXY and not USE_SB:
            self.client = httpx.AsyncClient(
                headers=HEADERS,
                proxies={"http": PROXY, "https": PROXY},
                verify=False,
            )
        else:
            self.client = httpx.AsyncClient(headers=HEADERS)

    async def fetch(self, url: str) -> httpx.Response:
        """Fetch URL with optional proxy."""
        if USE_SB and USE_PROXY:
            params = {"url": url}
            resp = await self.client.get(
                SCRAPING_BROWSER_EP,
                params=params,
                auth=(USER, PASSWORD),
                timeout=30,
                verify=False,
            )
        else:
            resp = await self.client.get(url, timeout=30)
        resp.raise_for_status()
        return resp

    async def scrape_calendar_page(self) -> List[Dict]:
        """Scrape the static calendar page (limited functionality)."""
        try:
            resp = await self.fetch(EVENTS_URL)
            soup = BeautifulSoup(resp.text, "html.parser")
            
            events = []
            # Look for any statically rendered events
            event_containers = soup.select(".event")
            
            for container in event_containers:
                data = {}
                
                title_el = container.select_one(".title")
                if title_el:
                    data["title"] = title_el.get_text(strip=True)
                
                date_el = container.select_one(".event-date span")
                if date_el:
                    data["date"] = date_el.get_text(strip=True)
                
                img_el = container.select_one("img")
                if img_el and img_el.get("src"):
                    data["image"] = img_el.get("src")
                
                link_el = container.select_one(".more-info")
                if link_el and link_el.get("href"):
                    data["link"] = link_el.get("href")
                
                desc_el = container.select_one("ul")
                if desc_el:
                    data["description"] = desc_el.get_text(separator=" ", strip=True)
                
                if data.get("title") and data.get("date"):
                    data["location"] = "Dubrovnik"
                    events.append(data)
            
            return events
            
        except Exception as e:
            print(f"Error scraping calendar page: {e}")
            return []

    async def close(self) -> None:
        """Close the HTTP client."""
        await self.client.aclose()


class DubrovnikPlaywrightScraper:
    """Playwright scraper for interactive calendar navigation."""

    async def scrape_with_playwright(self, months_ahead: int = 6) -> List[Dict]:
        """Scrape events using Playwright for calendar interaction."""
        try:
            from playwright.async_api import async_playwright
            
            all_events = []
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    locale='hr-HR',
                    timezone_id='Europe/Zagreb',
                )
                
                page = await context.new_page()
                
                try:
                    print(f"Navigating to {EVENTS_URL}")
                    await page.goto(EVENTS_URL, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Wait for calendar to load
                    await page.wait_for_selector("#calendar", timeout=10000)
                    
                    # Navigate through months
                    for month_offset in range(months_ahead + 1):
                        print(f"Processing month {month_offset + 1}/{months_ahead + 1}")
                        
                        # Get current month info
                        month_text = await page.text_content(".calendar-title-text .current-date")
                        print(f"Current month: {month_text}")
                        
                        # Find all event dates in current month
                        event_dates = await page.query_selector_all("button.calendar-dates-day.event-date")
                        print(f"Found {len(event_dates)} event dates in this month")
                        
                        # Click each event date
                        for i, date_button in enumerate(event_dates):
                            try:
                                # Click the date
                                await date_button.click()
                                await page.wait_for_timeout(2000)  # Wait for events to load
                                
                                # Extract events for this date
                                events = await self.extract_events_from_page(page)
                                print(f"Found {len(events)} events for date {i + 1}")
                                all_events.extend(events)
                                
                            except Exception as e:
                                print(f"Error clicking date {i + 1}: {e}")
                                continue
                        
                        # Move to next month (except on last iteration)
                        if month_offset < months_ahead:
                            try:
                                next_button = await page.query_selector("#nextMonth")
                                if next_button:
                                    await next_button.click()
                                    await page.wait_for_timeout(2000)
                                else:
                                    print("Next month button not found")
                                    break
                            except Exception as e:
                                print(f"Error navigating to next month: {e}")
                                break
                    
                except Exception as e:
                    print(f"Error during calendar scraping: {e}")
                
                await browser.close()
            
            return all_events
            
        except ImportError:
            print("Playwright not available")
            return []
        except Exception as e:
            print(f"Playwright error: {e}")
            return []

    async def extract_events_from_page(self, page) -> List[Dict]:
        """Extract events from the current page state."""
        try:
            events_data = await page.evaluate("""
                () => {
                    const events = [];
                    const eventContainers = document.querySelectorAll('.event');
                    
                    eventContainers.forEach(container => {
                        const data = {};
                        
                        // Extract title
                        const titleEl = container.querySelector('.title');
                        if (titleEl) {
                            data.title = titleEl.textContent?.trim() || '';
                        }
                        
                        // Extract date
                        const dateEl = container.querySelector('.event-date span');
                        if (dateEl) {
                            data.date = dateEl.textContent?.trim() || '';
                        }
                        
                        // Extract image
                        const imgEl = container.querySelector('img');
                        if (imgEl && imgEl.src) {
                            data.image = imgEl.src;
                        }
                        
                        // Extract link
                        const linkEl = container.querySelector('.more-info');
                        if (linkEl && linkEl.href) {
                            data.link = linkEl.href;
                        }
                        
                        // Extract description
                        const descEl = container.querySelector('ul');
                        if (descEl) {
                            data.description = descEl.textContent?.trim() || '';
                        }
                        
                        // Set default location
                        data.location = 'Dubrovnik';
                        
                        // Only add events with title and date
                        if (data.title && data.date) {
                            events.push(data);
                        }
                    });
                    
                    return events;
                }
            """)
            
            return events_data
            
        except Exception as e:
            print(f"Error extracting events: {e}")
            return []


class DubrovnikScraper:
    """High level scraper for Visit Dubrovnik events."""

    def __init__(self) -> None:
        self.requests_scraper = DubrovnikRequestsScraper()
        self.playwright_scraper = DubrovnikPlaywrightScraper()
        self.transformer = DubrovnikTransformer()

    async def scrape_events(self, months_ahead: int = 6, use_playwright: bool = True) -> List[EventCreate]:
        """Scrape events from Visit Dubrovnik calendar."""
        raw = []
        
        if use_playwright:
            # Try Playwright first for interactive calendar
            raw = await self.playwright_scraper.scrape_with_playwright(months_ahead=months_ahead)
            
            # If Playwright fails, fallback to requests
            if not raw:
                print("Playwright returned no results, falling back to requests approach")
                raw = await self.requests_scraper.scrape_calendar_page()
                await self.requests_scraper.close()
        else:
            # Use requests approach directly (limited functionality)
            raw = await self.requests_scraper.scrape_calendar_page()
            await self.requests_scraper.close()
        
        # Transform raw data to EventCreate objects
        events: List[EventCreate] = []
        for item in raw:
            event = self.transformer.transform(item)
            if event:
                events.append(event)
        
        return events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        """Save events to database with deduplication."""
        from sqlalchemy import select, tuple_

        from ..core.database import SessionLocal
        from ..models.event import Event

        if not events:
            return 0

        db = SessionLocal()
        try:
            event_dicts = [e.model_dump() for e in events]
            pairs = [(e["title"], e["date"]) for e in event_dicts]
            existing = db.execute(
                select(Event.title, Event.date).where(tuple_(Event.title, Event.date).in_(pairs))
            ).all()
            existing_pairs = set(existing)
            to_insert = [e for e in event_dicts if (e["title"], e["date"]) not in existing_pairs]
            
            saved_count = 0
            if to_insert:
                # Insert events individually to handle any constraint issues
                for event_data in to_insert:
                    try:
                        event = Event(**event_data)
                        db.add(event)
                        db.flush()  # Get the ID without committing
                        saved_count += 1
                    except Exception as e:
                        # Skip duplicate or invalid events
                        db.rollback()
                        print(f"Skipping event {event_data.get('title', 'Unknown')}: {e}")
                        # Continue with the next event
                        continue
                
                db.commit()
                return saved_count
            
            db.commit()
            return 0
        except Exception as e:
            db.rollback()
            print(f"Database error in Dubrovnik scraper: {e}")
            raise
        finally:
            db.close()


async def scrape_tzdubrovnik_events(months_ahead: int = 6) -> Dict:
    """Main function to scrape Visit Dubrovnik events."""
    scraper = DubrovnikScraper()
    try:
        events = await scraper.scrape_events(months_ahead=months_ahead)
        saved = scraper.save_events_to_database(events)
        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved,
            "message": f"Scraped {len(events)} events from Visit Dubrovnik, saved {saved} new events",
        }
    except Exception as e:
        return {"status": "error", "message": f"Visit Dubrovnik scraping failed: {e}"}