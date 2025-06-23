"""VisitOpatija.com events scraper with BrightData support."""

from __future__ import annotations

import asyncio
import os
import re
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

# Temporarily disabled until OpenAI dependency is added
# from ..core.llm_location_service import llm_location_service
from ..models.schemas import EventCreate

# BrightData configuration (shared across scrapers)
USER = os.getenv("BRIGHTDATA_USER", "demo_user")
PASSWORD = os.getenv("BRIGHTDATA_PASSWORD", "demo_password")
BRIGHTDATA_HOST_RES = "brd.superproxy.io"
BRIGHTDATA_PORT = int(os.getenv("BRIGHTDATA_PORT", 22225))
SCRAPING_BROWSER_EP = f"https://{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"
PROXY = f"http://{USER}:{PASSWORD}@{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"

USE_SB = os.getenv("USE_SCRAPING_BROWSER", "0") == "1"
USE_PROXY = os.getenv("USE_PROXY", "0") == "1"

BASE_URL = "https://www.visitopatija.com"
EVENTS_URL = f"{BASE_URL}/kalendar-dogadjanja"  # Croatian events calendar page

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0",
}


class VisitOpatijaTransformer:
    """Transform raw VisitOpatija event data to :class:`EventCreate`."""

    CRO_MONTHS = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        if not date_str:
            return None
        date_str = date_str.strip()
        
        # Handle Croatian date formats
        patterns = [
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})",  # DD.MM.YYYY
            r"(\d{4})-(\d{1,2})-(\d{1,2})",   # YYYY-MM-DD
            r"(\d{1,2})\s+(\w+)\s*(\d{4})",   # DD Month YYYY
            r"(\d{1,2})\.(\d{1,2})\.",        # DD.MM. (current year)
        ]
        
        for pattern in patterns:
            m = re.search(pattern, date_str, re.IGNORECASE)
            if m:
                try:
                    if pattern.endswith(r"\.(\d{4})"):  # Full date DD.MM.YYYY
                        day, month, year = m.groups()
                        return date(int(year), int(month), int(day))
                    elif pattern.startswith(r"(\d{4})"):  # YYYY-MM-DD
                        year, month, day = m.groups()
                        return date(int(year), int(month), int(day))
                    elif pattern.endswith(r"(\d{4})"):  # DD Month YYYY
                        day, month_name, year = m.groups()
                        month_num = VisitOpatijaTransformer.CRO_MONTHS.get(month_name.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                    elif pattern.endswith(r"\."):  # DD.MM. (assume current year)
                        day, month = m.groups()
                        from datetime import date as date_obj
                        current_year = date_obj.today().year
                        parsed_date = date(current_year, int(month), int(day))
                        # If date is in the past, assume next year
                        if parsed_date < date_obj.today():
                            parsed_date = date(current_year + 1, int(month), int(day))
                        return parsed_date
                except (ValueError, TypeError):
                    continue
        
        # Fallback: try to extract year and assume January 1st
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
    async def transform(cls, data: Dict) -> Optional[EventCreate]:
        try:
            name = cls.clean_text(data.get("title", ""))
            description = cls.clean_text(data.get("description", ""))
            
            # Extract specific venue from title and description if available
            raw_location = cls.clean_text(data.get("location", ""))
            if not raw_location or raw_location == "Opatija":
                # Try to extract specific venue from title/description
                text_content = f"{name} {description}".lower()
                if "amadria park" in text_content or "hotel royal" in text_content:
                    location = "Amadria Park Hotel Royal, Opatija"
                elif "park angiolina" in text_content or "angiolina" in text_content:
                    location = "Park Angiolina, Opatija"
                elif "villa angiolina" in text_content:
                    location = "Villa Angiolina, Opatija"
                elif "hotel milenij" in text_content:
                    location = "Hotel Milenij, Opatija"
                else:
                    # Temporarily disabled LLM fallback until OpenAI dependency is added
                    location = "Opatija"
                    # if llm_location_service.is_enabled():
                    #     try:
                    #         llm_result = await llm_location_service.extract_location(name, description, raw_location)
                    #         if llm_result and llm_result.confidence > 0.7 and "opatija" in llm_result.full_location.lower():
                    #             location = llm_result.full_location
                    #         else:
                    #             location = "Opatija"
                    #     except Exception as e:
                    #         print(f"LLM location extraction failed: {e}")
                    #         location = "Opatija"
            else:
                location = raw_location
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
                location=location or "Opatija",
                description=description or f"Event: {name}",
                price=price or "Check website",
                image=image,
                link=link,
                source="visitopatija",
                tags=[]  # Initialize tags as empty list to avoid ARRAY type issues
            )
        except Exception:
            return None


class VisitOpatijaRequestsScraper:
    """Scraper using httpx with optional BrightData proxy."""

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(headers=HEADERS)

    async def fetch(self, url: str) -> httpx.Response:
        try:
            if USE_SB and USE_PROXY:
                params = {"url": url}
                async with httpx.AsyncClient(
                    headers=HEADERS, auth=(USER, PASSWORD), verify=False
                ) as client:
                    resp = await client.get(
                        SCRAPING_BROWSER_EP, params=params, timeout=30
                    )
            elif USE_PROXY:
                async with httpx.AsyncClient(
                    headers=HEADERS,
                    proxies={"http": PROXY, "https": PROXY},
                    verify=False,
                ) as client:
                    resp = await client.get(url, timeout=30)
            else:
                async with httpx.AsyncClient(headers=HEADERS) as client:
                    resp = await client.get(url, timeout=30)
            resp.raise_for_status()
            return resp
        except httpx.HTTPError as e:
            raise RuntimeError(f"Request failed for {url}: {e}")

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

    def parse_listing_element(self, el: Tag) -> Dict:
        data: Dict[str, str] = {}
        
        # Get the raw text content
        full_text = el.get_text(separator=" ", strip=True)
        
        # Extract event title - look for patterns after event type keywords
        event_keywords = ["Manifestacija", "Koncert", "Festival", "Predstava", "Izložba", "Događaj"]
        title = ""
        
        for keyword in event_keywords:
            if keyword in full_text:
                # Try to extract title after the keyword and date
                import re
                pattern = rf"{keyword}[\d\.\-\s]*([A-ZŠĐČĆŽ][^:]+?)(?=Održavanje|Lokacija|$)"
                match = re.search(pattern, full_text)
                if match:
                    title = match.group(1).strip()
                    break
        
        # Fallback: look for capitalized words near the beginning
        if not title or len(title) < 3:
            import re
            # Look for capitalized phrases after dates
            date_pattern = r"[\d\.\-]+\s*([A-ZŠĐČĆŽ][^:]+?)(?=\s*\d|\s*Održavanje|\s*Lokacija|$)"
            match = re.search(date_pattern, full_text)
            if match:
                title = match.group(1).strip()
        
        # Final fallback: take first meaningful text
        if not title or len(title) < 3:
            words = full_text.split()
            meaningful_words = [w for w in words if len(w) > 2 and not w.isdigit() and "." not in w]
            if meaningful_words:
                title = " ".join(meaningful_words[:4])
        
        if title and "opširnije" not in title.lower():
            data["title"] = title
        
        # Extract dates using regex
        import re
        date_matches = re.findall(r'\d{1,2}\.\d{1,2}\.(?:\d{4})?', full_text)
        if date_matches:
            # Take the first complete date
            for date_match in date_matches:
                if len(date_match) >= 6:  # Has year
                    data["date"] = date_match
                    break
            if "date" not in data and date_matches:
                # Use first date and assume current year
                from datetime import date as date_obj
                current_year = date_obj.today().year
                data["date"] = f"{date_matches[0]}{current_year}"
        
        # Extract link - prefer non-"opširnije" links first
        links = el.select("a[href]")
        for link_el in links:
            href = link_el.get("href")
            link_text = link_el.get_text(strip=True)
            if href and "opširnije" not in link_text.lower():
                data["link"] = urljoin(BASE_URL, href)
                break
        
        # If no good link found, take any link
        if "link" not in data and links:
            href = links[0].get("href")
            if href:
                data["link"] = urljoin(BASE_URL, href)
        
        # Extract location from text patterns
        location_patterns = [
            r"Lokacija:([^O]+?)(?=Organizator|$)",
            r"(?:u\s+|@\s+)([A-ZŠĐČĆŽ][^,\n]+?)(?=\s|$)",
        ]
        for pattern in location_patterns:
            match = re.search(pattern, full_text)
            if match:
                location = match.group(1).strip()
                if location and len(location) > 2:
                    data["location"] = location
                    break
        
        # Extract time
        time_match = re.search(r'(\d{1,2}:\d{2})', full_text)
        if time_match:
            data["time"] = time_match.group(1)
        
        # Extract image
        img_el = el.select_one("img")
        if img_el and img_el.get("src"):
            data["image"] = img_el.get("src")

        return data

    async def scrape_events_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        resp = await self.fetch(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        events: List[Dict] = []
        containers: List[Tag] = []
        # Target the specific article structure found on Visit Opatija calendar page
        selectors = ["article.media-small.cnt-box", "article.cnt-box", "article"]
        for sel in selectors:
            found = soup.select(sel)
            if found:
                containers = found
                print(f"Found {len(found)} events using selector: {sel}")
                break

        for el in containers:
            if isinstance(el, Tag):
                data = self.parse_listing_element(el)
                link = data.get("link")
                if link:
                    try:
                        detail = await self.parse_event_detail(link)
                        data.update({k: v for k, v in detail.items() if v})
                    except Exception:
                        pass
                if data:
                    events.append(data)

        next_url = None
        next_link = soup.select_one('a[rel="next"], .pagination-next a, a.next')
        if next_link and next_link.get("href"):
            next_url = urljoin(url, next_link.get("href"))

        return events, next_url

    async def scrape_all_events(self, max_pages: int = 5) -> List[Dict]:
        all_events: List[Dict] = []
        current_url = EVENTS_URL
        page = 0
        while current_url and page < max_pages:
            page += 1
            events, next_url = await self.scrape_events_page(current_url)
            all_events.extend(events)
            if not next_url or not events:
                break
            current_url = next_url
            await asyncio.sleep(1)
        return all_events

    async def close(self) -> None:
        await self.client.aclose()


class VisitOpatijaScraper:
    """High level scraper for VisitOpatija.com."""

    def __init__(self) -> None:
        self.requests_scraper = VisitOpatijaRequestsScraper()
        self.transformer = VisitOpatijaTransformer()

    async def scrape_events(self, max_pages: int = 5) -> List[EventCreate]:
        raw = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
        events: List[EventCreate] = []
        for item in raw:
            event = await self.transformer.transform(item)
            if event:
                events.append(event)
        await self.requests_scraper.close()
        return events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        """Insert events using individual Event creation and return number of new rows."""
        if not events:
            return 0

        from ..core.database import SessionLocal
        from ..models.event import Event
        from sqlalchemy import select, tuple_

        db = SessionLocal()

        try:
            # Prepare incoming data for database
            event_dicts = []
            for e in events:
                event_dict = e.model_dump()
                # Remove id field as it's auto-generated by database
                event_dict.pop("id", None)
                event_dicts.append(event_dict)
            
            pairs = [(e["title"], e["date"]) for e in event_dicts]

            # Fetch all existing events for these (title, date) pairs
            existing = db.execute(
                select(Event.title, Event.date).where(
                    tuple_(Event.title, Event.date).in_(pairs)
                )
            ).all()
            existing_pairs = set(existing)

            # Filter to only new events
            to_insert = [
                e for e in event_dicts if (e["title"], e["date"]) not in existing_pairs
            ]

            if to_insert:
                # Insert each event individually to avoid bulk insert mapping issues
                saved_count = 0
                for event_data in to_insert:
                    try:
                        # Create Event object directly
                        event = Event(**event_data)
                        db.add(event)
                        db.flush()  # Get the ID without committing
                        saved_count += 1
                    except Exception as e:
                        # Skip duplicate or invalid events
                        db.rollback()
                        print(f"Skipping event {event_data.get('title', 'Unknown')}: {e}")
                        continue
                
                db.commit()
                return saved_count

            db.commit()
            return 0

        except Exception as e:
            print(f"Error saving events to database: {e}")
            db.rollback()
            raise
        finally:
            db.close()


async def scrape_visitopatija_events(max_pages: int = 5) -> Dict:
    scraper = VisitOpatijaScraper()
    try:
        events = await scraper.scrape_events(max_pages=max_pages)
        saved = scraper.save_events_to_database(events)
        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved,
            "message": f"Scraped {len(events)} events from VisitOpatija.com, saved {saved} new events",
        }
    except Exception as e:
        return {"status": "error", "message": f"VisitOpatija scraping failed: {e}"}
