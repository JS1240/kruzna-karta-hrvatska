"""VisitSplit.com events scraper with BrightData support."""

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

# BrightData configuration (reused from other scrapers)
USER = os.getenv("BRIGHTDATA_USER", "demo_user")
PASSWORD = os.getenv("BRIGHTDATA_PASSWORD", "demo_password")
BRIGHTDATA_HOST_RES = "brd.superproxy.io"
BRIGHTDATA_PORT = int(os.getenv("BRIGHTDATA_PORT", 22225))
SCRAPING_BROWSER_EP = f"https://{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"
PROXY = f"http://{USER}:{PASSWORD}@{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"

USE_SB = os.getenv("USE_SCRAPING_BROWSER", "0") == "1"
USE_PROXY = os.getenv("USE_PROXY", "0") == "1"

BASE_URL = "https://visitsplit.com"
EVENTS_URL = f"{BASE_URL}/hr/434/dogadanja"

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0",
}


class VisitSplitTransformer:
    """Transform raw VisitSplit event data to :class:`EventCreate`."""

    CRO_MONTHS = {
        "january": 1, "siječnja": 1, "siječanj": 1,
        "february": 2, "veljače": 2, "veljača": 2,
        "march": 3, "ožujka": 3, "ožujak": 3,
        "april": 4, "travnja": 4, "travanj": 4,
        "may": 5, "svibnja": 5, "svibanj": 5,
        "june": 6, "lipnja": 6, "lipanj": 6,
        "july": 7, "srpnja": 7, "srpanj": 7,
        "august": 8, "kolovoza": 8, "kolovoz": 8,
        "september": 9, "rujna": 9, "rujan": 9,
        "october": 10, "listopada": 10, "listopad": 10,
        "november": 11, "studenog": 11, "studeni": 11,
        "december": 12, "prosinca": 12, "prosinac": 12,
    }

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        if not date_str:
            return None
        date_str = date_str.strip()
        patterns = [
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})",
            r"(\d{4})-(\d{1,2})-(\d{1,2})",
            r"(\d{1,2})\s+(\w+)\s*(\d{4})",
        ]
        for pattern in patterns:
            m = re.search(pattern, date_str, re.IGNORECASE)
            if m:
                try:
                    if pattern.startswith("("):
                        day, month, year = m.groups()
                        if month.isdigit():
                            return date(int(year), int(month), int(day))
                        month_num = VisitSplitTransformer.CRO_MONTHS.get(month.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                    elif pattern.startswith(r"(\d{4})"):
                        year, month, day = m.groups()
                        return date(int(year), int(month), int(day))
                except (ValueError, TypeError):
                    continue
        year_match = re.search(r"(\d{4})", date_str)
        if year_match:
            try:
                return date(int(year_match.group(1)), 1, 1)
            except ValueError:
                pass
        return None

    @staticmethod
    def parse_time(time_str: str) -> str:
        if not time_str:
            return "20:00"
        m = re.search(r"(\d{1,2}):(\d{2})", time_str)
        if m:
            hour, minute = m.groups()
            return f"{int(hour):02d}:{minute}"
        m = re.search(r"(\d{1,2})h", time_str)
        if m:
            hour = m.group(1)
            return f"{int(hour):02d}:00"
        return "20:00"

    @staticmethod
    def clean_text(text: str) -> str:
        return " ".join(text.split()) if text else ""

    @classmethod
    def transform(cls, data: Dict) -> Optional[EventCreate]:
        try:
            name = cls.clean_text(data.get("title", ""))
            location = cls.clean_text(data.get("location", "Split"))
            description = cls.clean_text(data.get("description", ""))
            price = cls.clean_text(data.get("price", ""))

            date_str = data.get("date", "")
            parsed_date = cls.parse_date(date_str)
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

            if not name or len(name) < 3:
                return None

            return EventCreate(
                title=name,
                time=parsed_time,
                date=parsed_date,
                location=location or "Split",
                description=description or f"Event: {name}",
                price=price or "Check website",
                image=image,
                link=link,
                source="manual",
            )
        except Exception:
            return None


class VisitSplitRequestsScraper:
    """Scraper using httpx with optional BrightData proxy."""

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(headers=HEADERS)

    def generate_monthly_urls(self, start_date: Optional[datetime] = None) -> List[str]:
        """Generate URLs for 12 months starting from the given date."""
        if start_date is None:
            start_date = datetime.now()
        
        urls = []
        current_date = start_date.replace(day=1)  # Start from first day of month
        
        for _ in range(12):
            # Format: /hr/434/dogadanja/m-2025-07-1
            month_url = f"{BASE_URL}/hr/434/dogadanja/m-{current_date.year}-{current_date.month:02d}-1"
            urls.append(month_url)
            
            # Move to next month
            if current_date.month == 12:
                current_date = current_date.replace(year=current_date.year + 1, month=1)
            else:
                current_date = current_date.replace(month=current_date.month + 1)
        
        return urls

    def extract_next_month_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract next month URL from navigation button."""
        # Look for next month button: <a href="/hr/434/dogadanja/m-2025-07-1" class="kopa-button medium-button span-button">
        next_button = soup.select_one('a.kopa-button[href*="/hr/434/dogadanja/m-"]')
        if next_button and next_button.get('href'):
            return urljoin(BASE_URL, next_button.get('href'))
        return None

    async def fetch(self, url: str, max_retries: int = 3) -> httpx.Response:
        """Fetch URL with retry logic."""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if USE_SB and USE_PROXY:
                    params = {"url": url}
                    async with httpx.AsyncClient(headers=HEADERS, auth=(USER, PASSWORD), verify=False) as client:
                        resp = await client.get(SCRAPING_BROWSER_EP, params=params, timeout=30)
                elif USE_PROXY:
                    async with httpx.AsyncClient(headers=HEADERS, proxies={"http": PROXY, "https": PROXY}, verify=False) as client:
                        resp = await client.get(url, timeout=30)
                else:
                    async with httpx.AsyncClient(headers=HEADERS) as client:
                        resp = await client.get(url, timeout=30)
                resp.raise_for_status()
                return resp
                
            except httpx.HTTPError as e:
                last_exception = e
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    print(f"Request failed for {url} (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s: {e}")
                    await asyncio.sleep(wait_time)
                else:
                    print(f"All retry attempts failed for {url}")
        
        raise RuntimeError(f"Request failed for {url} after {max_retries} attempts: {last_exception}")

    async def parse_event_detail(self, url: str) -> Dict:
        resp = await self.fetch(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        data: Dict[str, str] = {}

        title_el = soup.select_one("h1")
        if title_el:
            data["title"] = title_el.get_text(strip=True)

        desc_el = soup.select_one(".description, .text, article")
        if desc_el:
            data["description"] = desc_el.get_text(separator=" ", strip=True)

        date_el = soup.find(string=re.compile(r"\d{4}"))
        if date_el:
            data["date"] = date_el.strip()

        time_el = soup.find(string=re.compile(r"\d{1,2}:\d{2}"))
        if time_el:
            data["time"] = time_el.strip()

        img_el = soup.select_one("img[src]")
        if img_el:
            data["image"] = img_el.get("src")

        loc_el = soup.select_one(".location, .venue, .place")
        if loc_el:
            data["location"] = loc_el.get_text(strip=True)

        price_el = soup.select_one(".price")
        if price_el:
            data["price"] = price_el.get_text(strip=True)

        return data

    def parse_calendar_cell(self, cell: Tag, day: str, month: int, year: int) -> List[Dict]:
        """Parse events from a calendar cell (td element)."""
        events = []
        
        # Look for event list in this cell
        event_list = cell.select_one("ul.events")
        if not event_list:
            return events
        
        # Parse each event in the cell
        event_items = event_list.select("li")
        for item in event_items:
            data = self.parse_calendar_event_item(item, day, month, year)
            if data:
                events.append(data)
        
        return events

    def parse_calendar_event_item(self, item: Tag, day: str, month: int, year: int) -> Optional[Dict]:
        """Parse individual event item from calendar cell."""
        data: Dict[str, str] = {}
        
        # Extract event title and link from main anchor tag
        main_link = item.select_one("a")
        if main_link:
            title = main_link.get_text(strip=True)
            if title:
                data["title"] = title
            
            # Check for link in href attribute
            href = main_link.get("href")
            if href:
                data["link"] = urljoin(BASE_URL, href)
        
        # Set date based on calendar position
        try:
            data["date"] = f"{int(day):02d}.{month:02d}.{year}"
        except (ValueError, TypeError):
            pass
        
        # Look for event popover with additional details
        popover = item.select_one(".event-popover")
        if popover:
            popover_data = self.parse_event_popover(popover)
            data.update(popover_data)
        
        return data if data.get("title") else None

    def parse_event_popover(self, popover: Tag) -> Dict:
        """Parse event details from popover div."""
        data: Dict[str, str] = {}
        
        # Extract title from h6 within popover
        title_el = popover.select_one("h6 a")
        if title_el:
            title = title_el.get_text(strip=True)
            if title and not data.get("title"):
                data["title"] = title
            
            # Get link from popover title
            href = title_el.get("href")
            if href:
                data["link"] = urljoin(BASE_URL, href)
        
        # Extract image from popover
        img_el = popover.select_one("img")
        if img_el and img_el.get("src"):
            data["image"] = urljoin(BASE_URL, img_el.get("src"))
        
        # Extract description/details from paragraph
        desc_el = popover.select_one("p")
        if desc_el:
            desc_text = desc_el.get_text(separator=" ", strip=True)
            if desc_text:
                data["description"] = desc_text
                
                # Try to extract location and time from description
                if "Lokacija:" in desc_text:
                    loc_match = re.search(r"Lokacija:\s*([^\n\r]+)", desc_text)
                    if loc_match:
                        data["location"] = loc_match.group(1).strip()
                
                if "Vrijeme:" in desc_text:
                    time_match = re.search(r"Vrijeme:\s*([^\n\r]+)", desc_text)
                    if time_match:
                        data["time"] = time_match.group(1).strip()
        
        return data

    async def scrape_calendar_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        """Scrape events from calendar page structure."""
        try:
            resp = await self.fetch(url)
            soup = BeautifulSoup(resp.text, "html.parser")

            events: List[Dict] = []
            
            # Find the calendar table
            calendar_table = soup.select_one("table.event-calendar")
            if not calendar_table:
                print(f"No calendar table found on page: {url}")
                return events, None

            # Extract year and month from URL or current context
            year, month = self.extract_year_month_from_url(url)
            
            # Find all calendar cells (td elements) - no tbody in this table
            calendar_cells = calendar_table.select("tr td")
            if not calendar_cells:
                print(f"No calendar cells found on page: {url}")
                return events, None
            
            for cell in calendar_cells:
                try:
                    # Extract day number from cell
                    day_span = cell.select_one("span.day")
                    if not day_span:
                        continue
                        
                    day = day_span.get_text(strip=True)
                    if not day.isdigit():
                        continue
                    
                    # Skip cells marked as "not-this-month"
                    if "not-this-month" in cell.get("class", []):
                        continue
                    
                    # Parse events from this calendar cell
                    cell_events = self.parse_calendar_cell(cell, day, month, year)
                    events.extend(cell_events)
                    
                except Exception as e:
                    print(f"Error parsing calendar cell: {e}")
                    continue

            # Look for next month navigation
            next_url = self.extract_next_month_url(soup)
            
            return events, next_url
            
        except Exception as e:
            print(f"Error scraping calendar page {url}: {e}")
            return [], None

    def extract_year_month_from_url(self, url: str) -> Tuple[int, int]:
        """Extract year and month from calendar URL."""
        # URL format: /hr/434/dogadanja/m-2025-07-1
        match = re.search(r"/m-(\d{4})-(\d{1,2})-", url)
        if match:
            year, month = match.groups()
            return int(year), int(month)
        
        # Fallback to current date
        now = datetime.now()
        return now.year, now.month

    async def scrape_events_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        """Legacy method - redirect to calendar scraping."""
        return await self.scrape_calendar_page(url)

    async def scrape_12_months_events(self, start_date: Optional[datetime] = None, 
                                     delay_between_months: float = 2.0,
                                     concurrent_requests: bool = False) -> List[Dict]:
        """Scrape events from 12 consecutive months with performance optimizations."""
        all_events: List[Dict] = []
        
        # Generate URLs for 12 months
        monthly_urls = self.generate_monthly_urls(start_date)
        
        if concurrent_requests:
            # Concurrent processing with semaphore for rate limiting
            semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests
            
            async def scrape_month_with_semaphore(url: str, month_num: int) -> List[Dict]:
                async with semaphore:
                    try:
                        print(f"Scraping month {month_num}/12: {url}")
                        events, _ = await self.scrape_calendar_page(url)
                        return events
                    except Exception as e:
                        print(f"Error scraping month {url}: {e}")
                        return []
            
            # Execute all months concurrently with rate limiting
            tasks = [scrape_month_with_semaphore(url, i+1) for i, url in enumerate(monthly_urls)]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, list):
                    all_events.extend(result)
                else:
                    print(f"Task failed with exception: {result}")
        else:
            # Sequential processing with delays (default, more respectful)
            for i, url in enumerate(monthly_urls):
                try:
                    print(f"Scraping month {i+1}/12: {url}")
                    events, _ = await self.scrape_calendar_page(url)
                    all_events.extend(events)
                    print(f"Found {len(events)} events in month {i+1}")
                    
                    # Add configurable delay between months
                    if i < len(monthly_urls) - 1:  # Don't sleep after last request
                        await asyncio.sleep(delay_between_months)
                        
                except Exception as e:
                    print(f"Error scraping month {url}: {e}")
                    continue
        
        print(f"Total events found across 12 months: {len(all_events)}")
        return all_events

    async def scrape_all_events(self, max_pages: int = 5) -> List[Dict]:
        """Main scraping method - now uses 12-month calendar approach."""
        return await self.scrape_12_months_events()

    async def close(self) -> None:
        await self.client.aclose()


class VisitSplitScraper:
    """High level scraper for VisitSplit.com."""

    def __init__(self) -> None:
        self.requests_scraper = VisitSplitRequestsScraper()
        self.transformer = VisitSplitTransformer()

    async def scrape_events(self, max_pages: int = 5, start_date: Optional[datetime] = None, 
                          concurrent: bool = False) -> List[EventCreate]:
        """Scrape events from VisitSplit calendar across 12 months."""
        raw = await self.requests_scraper.scrape_12_months_events(
            start_date=start_date, 
            concurrent_requests=concurrent
        )
        events: List[EventCreate] = []
        for item in raw:
            event = self.transformer.transform(item)
            if event:
                events.append(event)
        await self.requests_scraper.close()
        return events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        from sqlalchemy import select, tuple_
        from sqlalchemy.dialects.postgresql import insert

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
            if to_insert:
                stmt = insert(Event).values(to_insert)
                # Note: No unique constraint exists on title+date, so we'll insert without conflict handling
                db.execute(stmt)
                db.commit()
                return len(to_insert)
            db.commit()
            return 0
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


async def scrape_visitsplit_events(max_pages: int = 5) -> Dict:
    scraper = VisitSplitScraper()
    try:
        events = await scraper.scrape_events(max_pages=max_pages)
        saved = scraper.save_events_to_database(events)
        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved,
            "message": f"Scraped {len(events)} events from VisitSplit.com, saved {saved} new events",
        }
    except Exception as e:
        return {"status": "error", "message": f"VisitSplit scraping failed: {e}"}

