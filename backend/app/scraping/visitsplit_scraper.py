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


class VisitSplitDataTransformer:
    """Transform raw VisitSplit event data to :class:`EventCreate` with enhanced address extraction."""

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
                        month_num = VisitSplitDataTransformer.CRO_MONTHS.get(month.lower())
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
    
    @staticmethod
    def extract_location(data: Dict) -> str:
        """Extract and format location from VisitSplit event data with enhanced address support."""
        # Priority order: detected_address > venue_address > venue + city > location > city > venue (with Split) > default
        
        # Highest priority: detected_address from detailed scraping
        if data.get("detected_address"):
            return data["detected_address"].strip()
        
        # Second priority: venue_address from enhanced parsing
        if data.get("venue_address"):
            venue_address = data["venue_address"].strip()
            # If we have city info and it's not in venue_address, add it
            if data.get("city") and data["city"] not in venue_address:
                return f"{venue_address}, {data['city']}"
            return venue_address
        
        # Third priority: combine venue and city for fuller context
        venue = data.get("venue", "").strip()
        city = data.get("city", "Split").strip()
        
        if venue and city and city not in venue:
            return f"{venue}, {city}"
        elif venue:
            return venue
        
        # Fourth priority: location field from popover data
        location = data.get("location", "").strip()
        if location and location != "Split":
            if city and city not in location:
                return f"{location}, {city}"
            return location
        
        # Fifth priority: city (Split by default)
        if city:
            return city
        
        # Sixth priority: venue with Split added if not present
        if venue:
            if "Split" not in venue:
                return f"{venue}, Split"
            return venue
        
        # Fallback
        return "Split"
    
    @staticmethod
    def parse_location_from_text(text: str) -> Dict[str, str]:
        """Parse location information from event text using Split-specific patterns."""
        result = {}
        
        if not text:
            return result
        
        # Pattern 1: Lokacija field from popover data
        lokacija_match = re.search(r"Lokacija:\s*([^\n\r]+)", text, re.IGNORECASE)
        if lokacija_match:
            result["venue_address"] = lokacija_match.group(1).strip()
        
        # Pattern 2: Address in parentheses format: "(Obala kneza Branimira 19)"
        parentheses_match = re.search(r"\(([^)]+\d+[^)]*)\)", text)
        if parentheses_match:
            potential_address = parentheses_match.group(1).strip()
            # Validate it looks like an address (contains street name + number)
            if re.search(r"[A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+", potential_address):
                result["detected_address"] = potential_address
        
        # Pattern 3: Enhanced Split-specific venue recognition
        split_venues = [
            # Historic and cultural venues
            "Trg Peristil", "Podrumi Dioklecijanove palače", "HNK Split", "Galerija umjetnina",
            "Muzej grada Splita", "Arheološki muzej Split", "Etnografski muzej Split",
            "Gradska knjižnica Split", "Dom mladih Split", "Kino Zlatna vrata",
            "Kulturni centar Split", "Prokurative", "Riva Split", "Marjan",
            "Culture HUB Croatia", "Diocletian's Palace", "Split Park Festival",
            # Additional Split venues discovered
            "Kino Centaurus", "Art paviljon", "Galerija Kula", "Muzej hrvatskih arheoloških spomenika",
            "Umjetnička galerija Split", "Gradski muzej Split", "Split City Museum",
            "Dioklecijan's Palace", "Peristyle", "Cathedral of Saint Domnius",
            "Bacvice Beach", "Poljud Stadium", "Spaladium Arena"
        ]
        
        for venue in split_venues:
            if venue in text:
                if not result.get("venue"):
                    result["venue"] = venue
                break
        
        # Pattern 4: Enhanced Croatian address patterns for Split region
        address_patterns = [
            # Full address with postal code: "Plančićeva 2, 21000 Split"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,?\s*21000\s+Split)",
            # Street with number: "Plančićeva 2", "Obala kneza Branimira 19"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)",
            # Postal code with city: "21000 Split"
            r"(21000\s+Split(?:[^\n,]*)?)",
            # Split-specific street patterns with Croatian prefixes
            r"((?:Obala|Riva|Trg|Ulica|Put|Poljana|Peristil|Prokurative)\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]*\d*[a-z]?)",
            # General Croatian address with number (broader pattern)
            r"([A-ZČĆĐŠŽ][a-zčćđšž]{2,}\s+(?:[A-ZČĆĐŠŽ][a-zčćđšž\s]*\s+)?\d+[a-z]?)"
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text)
            if matches:
                result["detected_address"] = matches[0].strip()
                break
        
        # Extract Split as city if present
        if "Split" in text and not result.get("city"):
            result["city"] = "Split"
        
        return result

    @classmethod
    def transform(cls, data: Dict) -> Optional[EventCreate]:
        try:
            name = cls.clean_text(data.get("title", ""))
            
            # Parse location information from description and other text fields
            full_text = data.get("description", "") or data.get("full_text", "")
            location_info = cls.parse_location_from_text(full_text)
            
            # Merge parsed location info with existing data
            enhanced_data = {**data, **location_info}
            
            # Use enhanced location extraction
            location = cls.extract_location(enhanced_data)
            
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

    async def fetch_event_details(self, event_url: str) -> Dict:
        """Fetch detailed address information from individual event page."""
        try:
            resp = await self.fetch(event_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            details = {}
            
            # Extract enhanced location information from event detail page
            page_text = soup.get_text()
            
            # Extract Lokacija field from detail pages
            lokacija_match = re.search(r"Lokacija:\s*([^\n\r]+)", page_text, re.IGNORECASE)
            if lokacija_match:
                details["venue_address"] = lokacija_match.group(1).strip()
            
            # Look for detailed address patterns in page content
            address_patterns = [
                # Address in parentheses: "(Obala kneza Branimira 19)"
                r"\(([^)]+\d+[^)]*)\)",
                # Full address: "Plančićeva 2"
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)",
                # Split postal code + address: "21000 Split, Riva 12"
                r"(21000\s+Split[^\n]*)"
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    # Get the first clean match that looks like an address
                    for match in matches:
                        match = match.strip()
                        if re.search(r"[A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+", match):
                            details["detected_address"] = match
                            break
                    if details.get("detected_address"):
                        break
            
            # Extract Split-specific venue information
            split_venues = [
                # Historic and cultural venues
                "Trg Peristil", "Podrumi Dioklecijanove palače", "HNK Split", "Galerija umjetnina",
                "Muzej grada Splita", "Arheološki muzej Split", "Etnografski muzej Split",
                "Gradska knjižnica Split", "Dom mladih Split", "Kino Zlatna vrata",
                "Kulturni centar Split", "Prokurative", "Riva Split", "Marjan",
                "Culture HUB Croatia", "Diocletian's Palace", "Split Park Festival",
                # Additional Split venues
                "Kino Centaurus", "Art paviljon", "Galerija Kula", "Muzej hrvatskih arheoloških spomenika",
                "Umjetnička galerija Split", "Gradski muzej Split", "Split City Museum",
                "Dioklecijan's Palace", "Peristyle", "Cathedral of Saint Domnius"
            ]
            
            for venue in split_venues:
                if venue in page_text and not details.get("venue"):
                    details["venue"] = venue
                    break
            
            # Ensure Split is recognized as city
            if "Split" in page_text and not details.get("city"):
                details["city"] = "Split"
            
            # Store full page text for further processing
            details["full_text"] = page_text
            
            return details
            
        except Exception as e:
            print(f"Error fetching event details from {event_url}: {e}")
            return {}

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
                
                # Enhanced location extraction from description
                if "Lokacija:" in desc_text:
                    loc_match = re.search(r"Lokacija:\s*([^\n\r]+)", desc_text)
                    if loc_match:
                        location_text = loc_match.group(1).strip()
                        data["location"] = location_text
                        
                        # Check if location contains address in parentheses
                        parentheses_match = re.search(r"\(([^)]+\d+[^)]*)\)", location_text)
                        if parentheses_match:
                            potential_address = parentheses_match.group(1).strip()
                            # Validate it looks like an address
                            if re.search(r"[A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+", potential_address):
                                data["detected_address"] = potential_address
                                # Extract venue name before parentheses
                                venue_match = re.search(r"^([^(]+)\s*\(", location_text)
                                if venue_match:
                                    data["venue"] = venue_match.group(1).strip()
                
                # Extract time information
                if "Vrijeme:" in desc_text:
                    time_match = re.search(r"Vrijeme:\s*([^\n\r]+)", desc_text)
                    if time_match:
                        data["time"] = time_match.group(1).strip()
                
                # Look for Split-specific venues in description
                split_venues = [
                    # Historic and cultural venues  
                    "Trg Peristil", "Podrumi Dioklecijanove palače", "HNK Split", "Galerija umjetnina",
                    "Muzej grada Splita", "Arheološki muzej Split", "Etnografski muzej Split",
                    "Gradska knjižnica Split", "Dom mladih Split", "Kino Zlatna vrata",
                    "Kulturni centar Split", "Prokurative", "Riva Split", "Marjan",
                    "Culture HUB Croatia", "Diocletian's Palace", "Split Park Festival",
                    # Additional Split venues
                    "Kino Centaurus", "Art paviljon", "Galerija Kula"
                ]
                
                for venue in split_venues:
                    if venue in desc_text and not data.get("venue"):
                        data["venue"] = venue
                        break
                
                # Apply general Croatian address pattern detection
                if not data.get("detected_address"):
                    address_patterns = [
                        # Address in parentheses format
                        r"\(([^)]+\d+[^)]*)\)",
                        # Street name with number: "Plančićeva 2"
                        r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)",
                        # Split postal code patterns
                        r"(21000\s+Split[^\n]*)"
                    ]
                    
                    for pattern in address_patterns:
                        matches = re.findall(pattern, desc_text)
                        if matches:
                            for match in matches:
                                match = match.strip()
                                # Validate it's a real address
                                if re.search(r"[A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+", match):
                                    data["detected_address"] = match
                                    break
                            if data.get("detected_address"):
                                break
                
                # Ensure Split is recognized as city
                if "Split" in desc_text:
                    data["city"] = "Split"
        
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


class VisitSplitPlaywrightScraper:
    """Playwright scraper for enhanced VisitSplit calendar and detail page extraction."""

    async def fetch_event_details(self, page, event_url: str) -> Dict:
        """Fetch detailed address information from individual event page using Playwright."""
        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for content to load
            
            # Extract detailed location information from event detail page
            event_details = await page.evaluate("""
                () => {
                    const details = {};
                    
                    // Extract text content from the entire page
                    const pageText = document.body.textContent;
                    
                    // Extract Lokacija field
                    const locationMatch = pageText.match(/Lokacija:\\s*([^\\n\\r]+)/i);
                    if (locationMatch) {
                        details.venue_address = locationMatch[1].trim();
                    }
                    
                    // Look for address patterns in parentheses: "(Obala kneza Branimira 19)"
                    const parenthesesPattern = /\\(([^)]+\\d+[^)]*)\\)/g;
                    const parenthesesMatches = [...pageText.matchAll(parenthesesPattern)];
                    if (parenthesesMatches.length > 0) {
                        for (const match of parenthesesMatches) {
                            const potentialAddress = match[1].trim();
                            // Validate it looks like an address (Croatian pattern)
                            if (/[A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+/.test(potentialAddress)) {
                                details.detected_address = potentialAddress;
                                break;
                            }
                        }
                    }
                    
                    // Look for Split-specific venues
                    const splitVenues = [
                        "Trg Peristil", "Podrumi Dioklecijanove palače", "HNK Split", "Galerija umjetnina",
                        "Muzej grada Splita", "Arheološki muzej Split", "Etnografski muzej Split",
                        "Gradska knjižnica Split", "Dom mladih Split", "Kino Zlatna vrata",
                        "Kulturni centar Split", "Prokurative", "Riva Split", "Marjan",
                        "Culture HUB Croatia", "Diocletian's Palace", "Split Park Festival",
                        "Kino Centaurus", "Art paviljon", "Galerija Kula"
                    ];
                    
                    for (const venue of splitVenues) {
                        if (pageText.includes(venue)) {
                            details.venue = venue;
                            break;
                        }
                    }
                    
                    // Look for general Croatian address patterns
                    if (!details.detected_address) {
                        const addressPatterns = [
                            // Street name with number: "Plančićeva 2"
                            /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?)/g,
                            // Split postal code + address: "21000 Split, Riva 12"
                            /(21000\\s+Split[^\\n]*)/g
                        ];
                        
                        for (const pattern of addressPatterns) {
                            const matches = [...pageText.matchAll(pattern)];
                            if (matches.length > 0) {
                                for (const match of matches) {
                                    const potentialAddress = match[1].trim();
                                    if (/[A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+/.test(potentialAddress)) {
                                        details.detected_address = potentialAddress;
                                        break;
                                    }
                                }
                                if (details.detected_address) break;
                            }
                        }
                    }
                    
                    // Ensure Split is recognized as city
                    if (pageText.includes("Split")) {
                        details.city = "Split";
                    }
                    
                    // Store full page text for further processing
                    details.full_text = pageText;
                    
                    return details;
                }
            """)
            
            return event_details
            
        except Exception as e:
            print(f"Error fetching event details from {event_url}: {e}")
            return {}

    async def scrape_with_playwright(self, start_url: str = None, max_pages: int = 5, fetch_details: bool = False) -> List[Dict]:
        """Scrape events using Playwright with enhanced calendar navigation and address extraction."""
        try:
            from playwright.async_api import async_playwright
            
            all_events = []
            
            async with async_playwright() as p:
                # Configure browser with proxy if needed
                if USE_PROXY:
                    browser = await p.chromium.launch(
                        headless=True,
                        proxy={"server": PROXY}
                    )
                else:
                    browser = await p.chromium.launch(headless=True)
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                try:
                    # Start with main events page or generate monthly URLs
                    base_url = start_url or f"{BASE_URL}/hr/434/dogadanja"
                    print(f"Navigating to {base_url}")
                    await page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Handle cookie consent if present
                    try:
                        cookie_button = await page.query_selector('button:has-text("Prihvati")')
                        if cookie_button:
                            await cookie_button.click()
                            await page.wait_for_timeout(1000)
                    except:
                        pass
                    
                    # Generate monthly URLs for comprehensive scraping
                    monthly_urls = []
                    current_date = datetime.now()
                    for i in range(max_pages):
                        month_url = f"{BASE_URL}/hr/434/dogadanja/m-{current_date.year}-{current_date.month:02d}-1"
                        monthly_urls.append(month_url)
                        # Move to next month
                        if current_date.month == 12:
                            current_date = current_date.replace(year=current_date.year + 1, month=1)
                        else:
                            current_date = current_date.replace(month=current_date.month + 1)
                    
                    for i, month_url in enumerate(monthly_urls):
                        print(f"Scraping month {i+1}/{len(monthly_urls)}: {month_url}")
                        
                        try:
                            await page.goto(month_url, wait_until="domcontentloaded", timeout=30000)
                            await page.wait_for_timeout(3000)
                            
                            # Extract events from calendar using JavaScript
                            events_data = await page.evaluate("""
                                () => {
                                    const events = [];
                                    
                                    // Find calendar table
                                    const calendarTable = document.querySelector('table.event-calendar');
                                    if (!calendarTable) return events;
                                    
                                    // Find all calendar cells with events
                                    const cells = calendarTable.querySelectorAll('tr td');
                                    
                                    cells.forEach(cell => {
                                        // Check if cell has day number
                                        const daySpan = cell.querySelector('span.day');
                                        if (!daySpan) return;
                                        
                                        const day = daySpan.textContent.trim();
                                        if (!day.match(/^\\d+$/)) return;
                                        
                                        // Skip cells marked as "not-this-month"
                                        if (cell.classList.contains('not-this-month')) return;
                                        
                                        // Look for event list in this cell
                                        const eventList = cell.querySelector('ul.events');
                                        if (!eventList) return;
                                        
                                        const eventItems = eventList.querySelectorAll('li');
                                        eventItems.forEach(item => {
                                            const eventData = {};
                                            
                                            // Extract title and link from main anchor
                                            const mainLink = item.querySelector('a');
                                            if (mainLink) {
                                                eventData.title = mainLink.textContent.trim();
                                                eventData.link = mainLink.href;
                                            }
                                            
                                            // Set date based on calendar position
                                            const urlMatch = window.location.href.match(/m-(\\d{4})-(\\d{1,2})-/);
                                            if (urlMatch) {
                                                const year = urlMatch[1];
                                                const month = urlMatch[2];
                                                eventData.date = `${day.padStart(2, '0')}.${month.padStart(2, '0')}.${year}`;
                                            }
                                            
                                            // Look for popover with additional details
                                            const popover = item.querySelector('.event-popover');
                                            if (popover) {
                                                // Extract enhanced popover data
                                                const popoverTitle = popover.querySelector('h6 a');
                                                if (popoverTitle && !eventData.title) {
                                                    eventData.title = popoverTitle.textContent.trim();
                                                    eventData.link = popoverTitle.href;
                                                }
                                                
                                                const popoverImg = popover.querySelector('img');
                                                if (popoverImg && popoverImg.src) {
                                                    eventData.image = popoverImg.src;
                                                }
                                                
                                                const popoverDesc = popover.querySelector('p');
                                                if (popoverDesc) {
                                                    const descText = popoverDesc.textContent;
                                                    eventData.description = descText;
                                                    
                                                    // Extract location from popover description
                                                    const locationMatch = descText.match(/Lokacija:\\s*([^\\n\\r]+)/i);
                                                    if (locationMatch) {
                                                        eventData.location = locationMatch[1].trim();
                                                        
                                                        // Check for address in parentheses
                                                        const parenthesesMatch = locationMatch[1].match(/\\(([^)]+\\d+[^)]*)\\)/);
                                                        if (parenthesesMatch) {
                                                            eventData.detected_address = parenthesesMatch[1].trim();
                                                        }
                                                    }
                                                    
                                                    // Extract time
                                                    const timeMatch = descText.match(/Vrijeme:\\s*([^\\n\\r]+)/i);
                                                    if (timeMatch) {
                                                        eventData.time = timeMatch[1].trim();
                                                    }
                                                }
                                            }
                                            
                                            // Only add if we have meaningful data
                                            if (eventData.title || eventData.link) {
                                                events.push(eventData);
                                            }
                                        });
                                    });
                                    
                                    return events;
                                }
                            """)
                            
                            valid_events = [
                                event for event in events_data
                                if event.get("title") or event.get("link")
                            ]
                            
                            # Fetch detailed address information if requested
                            if fetch_details and valid_events:
                                print(f"Fetching detailed address info for {len(valid_events)} events...")
                                enhanced_events = []
                                
                                for j, event in enumerate(valid_events):
                                    if event.get("link"):
                                        try:
                                            # Rate limiting - fetch details for every 2nd event
                                            if j % 2 == 0:
                                                details = await self.fetch_event_details(page, event["link"])
                                                if details:
                                                    # Merge detailed information
                                                    event.update(details)
                                                    print(f"Enhanced event {j+1}/{len(valid_events)}: {event.get('title', 'Unknown')}")
                                                
                                                # Add delay between detail fetches
                                                await page.wait_for_timeout(1500)
                                            
                                            enhanced_events.append(event)
                                            
                                        except Exception as e:
                                            print(f"Error fetching details for event {event.get('title', 'Unknown')}: {e}")
                                            enhanced_events.append(event)  # Add original event even if detail fetch fails
                                    else:
                                        enhanced_events.append(event)
                                
                                valid_events = enhanced_events
                            
                            all_events.extend(valid_events)
                            print(f"Month {i+1}: Found {len(valid_events)} events (Total: {len(all_events)})")
                            
                            # Add delay between months
                            if i < len(monthly_urls) - 1:
                                await page.wait_for_timeout(2000)
                        
                        except Exception as e:
                            print(f"Error scraping month {month_url}: {e}")
                            continue
                    
                except Exception as e:
                    print(f"Error during scraping: {e}")
                
                await browser.close()
            
            return all_events
            
        except ImportError:
            print("Playwright not available, falling back to requests approach")
            return []
        except Exception as e:
            print(f"Playwright error: {e}")
            return []


class VisitSplitScraper:
    """High level scraper for VisitSplit.com."""

    def __init__(self) -> None:
        self.requests_scraper = VisitSplitRequestsScraper()
        self.playwright_scraper = VisitSplitPlaywrightScraper()
        self.transformer = VisitSplitDataTransformer()

    async def scrape_events(self, max_pages: int = 5, start_date: Optional[datetime] = None, 
                          concurrent: bool = False, use_playwright: bool = True, 
                          fetch_details: bool = False) -> List[EventCreate]:
        """Scrape events from VisitSplit calendar with optional enhanced address extraction."""
        all_events: List[EventCreate] = []
        raw_events = []
        
        if use_playwright:
            # Try Playwright first for enhanced extraction
            print("Using Playwright for enhanced VisitSplit scraping...")
            try:
                raw_events = await self.playwright_scraper.scrape_with_playwright(
                    max_pages=max_pages,
                    fetch_details=fetch_details
                )
                print(f"Playwright extracted {len(raw_events)} raw events")
            except Exception as e:
                print(f"Playwright failed: {e}, falling back to requests approach")
                raw_events = []
        
        # If Playwright fails or is disabled, use requests approach
        if not raw_events:
            print("Using requests/BeautifulSoup approach...")
            try:
                raw_events = await self.requests_scraper.scrape_12_months_events(
                    start_date=start_date, 
                    concurrent_requests=concurrent
                )
                
                # Enhance with detail fetching if requested
                if fetch_details and raw_events:
                    print(f"Fetching detailed address info for {len(raw_events)} events...")
                    enhanced_events = []
                    
                    for i, event in enumerate(raw_events):
                        if event.get("link"):
                            try:
                                # Rate limiting - fetch details for every 3rd event
                                if i % 3 == 0:
                                    details = await self.requests_scraper.fetch_event_details(event["link"])
                                    if details:
                                        # Merge detailed information
                                        event.update(details)
                                        print(f"Enhanced event {i+1}/{len(raw_events)}: {event.get('title', 'Unknown')}")
                                    
                                    # Add delay between detail fetches
                                    await asyncio.sleep(1)
                                
                                enhanced_events.append(event)
                                
                            except Exception as e:
                                print(f"Error fetching details for event {event.get('title', 'Unknown')}: {e}")
                                enhanced_events.append(event)  # Add original event even if detail fetch fails
                        else:
                            enhanced_events.append(event)
                    
                    raw_events = enhanced_events
                
                print(f"Requests approach extracted {len(raw_events)} raw events")
            except Exception as e:
                print(f"Requests approach also failed: {e}")
                raw_events = []
        
        # Transform raw data to EventCreate objects
        for raw_event in raw_events:
            event = self.transformer.transform(raw_event)
            if event:
                all_events.append(event)
        
        await self.requests_scraper.close()
        print(f"Transformed {len(all_events)} valid events from {len(raw_events)} raw events")
        return all_events

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


async def scrape_visitsplit_events(max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> Dict:
    scraper = VisitSplitScraper()
    try:
        events = await scraper.scrape_events(
            max_pages=max_pages,
            use_playwright=use_playwright,
            fetch_details=fetch_details
        )
        saved = scraper.save_events_to_database(events)
        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved,
            "message": f"Scraped {len(events)} events from VisitSplit.com, saved {saved} new events" + 
                      (f" (with enhanced address extraction)" if fetch_details else ""),
        }
    except Exception as e:
        return {"status": "error", "message": f"VisitSplit scraping failed: {e}"}

