"""VisitOpatija.com events scraper with BrightData support."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

# Temporarily disabled until OpenAI dependency is added
# from backend.app.core.llm_location_service import llm_location_service
from backend.app.models.schemas import EventCreate

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

# Configure logging
logger = logging.getLogger(__name__)


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

    @staticmethod
    def parse_location_from_text(text: str) -> Dict[str, str]:
        """Parse location information from event text using Opatija-specific patterns."""
        result = {}
        
        if not text:
            return result
        
        # Pattern 1: Google Maps links with coordinates (unique to Visit Opatija)
        maps_pattern = r"\[([^\]]+)\]\(https://www\.google\.hr/maps/place/[\d\.,]+\)"
        maps_match = re.search(maps_pattern, text)
        if maps_match:
            venue_name = maps_match.group(1).strip()
            result["venue"] = venue_name
            result["detected_address"] = f"{venue_name}, Opatija"
        
        # Pattern 2: Croatian address patterns for Opatija region
        address_patterns = [
            # Full address with Opatija region cities
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,?\s*(?:51410|51414|51415|51417)\s+(?:Opatija|Ika|Volosko|Veprinac))",
            # Street with number in Opatija
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)\s*,?\s*Opatija",
            # Opatija region specific venues with addresses
            r"((?:Amadria\s+Park|Hotel\s+\w+|Villa\s+\w+|Park\s+\w+|Ljetna\s+pozornica)\s+[^,\n]+)(?:\s*,?\s*(?:u\s+)?Opatija)?",
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                result["detected_address"] = matches[0].strip()
                if "Opatija" not in result["detected_address"]:
                    result["detected_address"] += ", Opatija"
                break
        
        # Pattern 3: Extract Opatija region cities
        city_patterns = [
            r"\b(Opatija|Ika|Volosko|Veprinac|Lovran|Matulji|Mošćenička Draga)\b"
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["city"] = match.group(1)
                break
        
        # Pattern 4: Extract venue information specific to Opatija
        venue_patterns = [
            r"(Amadria\s+Park\s+Hotel\s+\w+)",
            r"(Hotel\s+\w+(?:\s+\w+)?)",
            r"(Villa\s+\w+)",
            r"(Park\s+Angiolina)",
            r"(Ljetna\s+pozornica(?:\s+u\s+Opatija)?)",
            r"((?:HNK|Kazalište|Kino|Galerija|Muzej)\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]*)",
        ]
        
        for pattern in venue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["venue"] = match.group(1).strip()
                break
        
        return result

    @staticmethod
    def extract_location(data: Dict) -> str:
        """Extract and format location with priority-based system for Opatija region."""
        # Priority order: detected_address > venue_address > venue + city > location > city > venue (with Opatija) > default
        
        # Highest priority: detected_address from detailed scraping or Google Maps
        if data.get("detected_address"):
            return data["detected_address"].strip()
        
        # Second priority: venue_address field (if available)
        if data.get("venue_address"):
            venue_address = data["venue_address"].strip()
            if data.get("city") and data["city"] not in venue_address:
                return f"{venue_address}, {data['city']}"
            return venue_address
        
        # Third priority: combine venue and city for specific context
        venue = data.get("venue", "").strip()
        city = data.get("city", "").strip()
        
        if venue and city:
            return f"{venue}, {city}"
        
        # Fourth priority: location field
        if data.get("location"):
            location = data["location"].strip()
            if city and city not in location:
                return f"{location}, {city}"
            return location
        
        # Fifth priority: city only
        if city:
            return city
        
        # Sixth priority: venue with Opatija assumption (for Opatija-specific venues)
        if venue:
            opatija_venues = [
                "amadria park", "hotel", "villa", "park angiolina", 
                "ljetna pozornica", "hnk", "kazalište", "kino", "galerija", "muzej"
            ]
            if any(ov in venue.lower() for ov in opatija_venues):
                return f"{venue}, Opatija"
            return venue
        
        # Fallback
        return "Opatija"

    @classmethod
    async def transform(cls, data: Dict) -> Optional[EventCreate]:
        try:
            name = cls.clean_text(data.get("title", ""))
            description = cls.clean_text(data.get("description", ""))
            
            # Parse location information from text content using enhanced patterns
            full_text = data.get("full_text", "") or f"{name} {description}"
            location_info = cls.parse_location_from_text(full_text)
            
            # Merge parsed location info with existing data
            enhanced_data = {**data, **location_info}
            
            # Use enhanced location extraction with priority system
            location = cls.extract_location(enhanced_data)
            
            # Fallback to original location extraction if enhanced method fails
            if not location or location == "Opatija":
                raw_location = cls.clean_text(data.get("location", ""))
                if raw_location and raw_location != "Opatija":
                    location = raw_location
                else:
                    # Try to extract specific venue from title/description for known Opatija venues
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
                        location = "Opatija"
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

    async def fetch_event_details(self, url: str) -> Dict:
        """Fetch detailed address information from individual event page."""
        try:
            resp = await self.fetch(url)
            soup = BeautifulSoup(resp.text, "html.parser")
            details = {}
            
            # Get full page text for comprehensive analysis
            full_text = soup.get_text(separator=" ", strip=True)
            details["full_text"] = full_text
            
            # Parse location information using enhanced patterns
            location_info = VisitOpatijaTransformer.parse_location_from_text(full_text)
            details.update(location_info)
            
            # Enhanced venue detection using multiple selectors
            venue_selectors = [
                ".location", ".venue", ".place", ".lokacija", ".adresa", ".mjesto",
                ".event-location", ".venue-info", "[class*='location']", "[class*='venue']"
            ]
            
            for selector in venue_selectors:
                venue_el = soup.select_one(selector)
                if venue_el:
                    venue_text = venue_el.get_text(strip=True)
                    if venue_text and len(venue_text) > 2:
                        details["venue_address"] = venue_text
                        break
            
            # Look for Google Maps links (unique to Visit Opatija)
            map_links = soup.find_all("a", href=re.compile(r"google\.hr/maps/place"))
            if map_links:
                for link in map_links:
                    link_text = link.get_text(strip=True)
                    if link_text and len(link_text) > 3:
                        details["detected_address"] = f"{link_text}, Opatija"
                        details["venue"] = link_text
                        break
            
            # Enhanced address pattern detection in full page content
            if not details.get("detected_address"):
                # Look for Opatija region specific address patterns
                address_patterns = [
                    # Full address with postal codes for Opatija region
                    r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,?\s*(?:51410|51414|51415|51417)\s+(?:Opatija|Ika|Volosko|Veprinac))",
                    # Street with number followed by Opatija
                    r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)\s*,?\s*Opatija",
                    # Opatija venues with detailed location
                    r"((?:Amadria\s+Park|Hotel\s+\w+|Villa\s+\w+|Park\s+\w+|Ljetna\s+pozornica)\s+[^,\n]{3,50})(?:\s*,?\s*(?:u\s+)?Opatija)?",
                ]
                
                for pattern in address_patterns:
                    matches = re.findall(pattern, full_text, re.IGNORECASE)
                    if matches:
                        address = matches[0].strip()
                        if "Opatija" not in address:
                            address += ", Opatija"
                        details["detected_address"] = address
                        break
            
            # Extract additional venue information from structured content
            if not details.get("venue"):
                venue_keywords = ["Hotel", "Villa", "Park", "Galerija", "Muzej", "Kazalište", "Kino"]
                for keyword in venue_keywords:
                    venue_match = re.search(rf"({keyword}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]*)", full_text, re.IGNORECASE)
                    if venue_match:
                        details["venue"] = venue_match.group(1).strip()
                        break
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching event details from {url}: {e}")
            return {}

    async def parse_event_detail(self, url: str) -> Dict:
        """Enhanced parse_event_detail with comprehensive address pattern detection."""
        resp = await self.fetch(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        data: Dict[str, str] = {}

        # Get full page text for comprehensive analysis
        full_text = soup.get_text(separator=" ", strip=True)
        data["full_text"] = full_text

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

        # Enhanced location extraction using multiple selectors
        location_selectors = [
            ".location", ".venue", ".place", ".lokacija", ".adresa", ".mjesto",
            ".event-location", ".venue-info", "[class*='location']", "[class*='venue']"
        ]
        
        for selector in location_selectors:
            loc_el = soup.select_one(selector)
            if loc_el:
                location_text = loc_el.get_text(strip=True)
                if location_text and len(location_text) > 2:
                    data["location"] = location_text
                    break

        price_el = soup.select_one(".price")
        if price_el:
            data["price"] = price_el.get_text(strip=True)

        # Parse location information using enhanced Opatija-specific patterns
        location_info = VisitOpatijaTransformer.parse_location_from_text(full_text)
        data.update(location_info)
        
        # Look for Google Maps links (unique to Visit Opatija)
        map_links = soup.find_all("a", href=re.compile(r"google\.hr/maps/place"))
        if map_links:
            for link in map_links:
                link_text = link.get_text(strip=True)
                if link_text and len(link_text) > 3:
                    data["detected_address"] = f"{link_text}, Opatija"
                    data["venue"] = link_text
                    break
        
        # Enhanced address pattern detection in full page content
        if not data.get("detected_address"):
            # Look for Opatija region specific address patterns
            address_patterns = [
                # Full address with postal codes for Opatija region
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,?\s*(?:51410|51414|51415|51417)\s+(?:Opatija|Ika|Volosko|Veprinac))",
                # Street with number followed by Opatija
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)\s*,?\s*Opatija",
                # Opatija venues with detailed location
                r"((?:Amadria\s+Park|Hotel\s+\w+|Villa\s+\w+|Park\s+\w+|Ljetna\s+pozornica)\s+[^,\n]{3,50})(?:\s*,?\s*(?:u\s+)?Opatija)?",
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    address = matches[0].strip()
                    if "Opatija" not in address:
                        address += ", Opatija"
                    data["detected_address"] = address
                    break
        
        # Extract venue information from structured content
        if not data.get("venue"):
            venue_keywords = ["Hotel", "Villa", "Park", "Galerija", "Muzej", "Kazalište", "Kino"]
            for keyword in venue_keywords:
                venue_match = re.search(rf"({keyword}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]*)", full_text, re.IGNORECASE)
                if venue_match:
                    data["venue"] = venue_match.group(1).strip()
                    break

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
        
        # Enhanced location extraction from text patterns using Opatija-specific patterns
        data["full_text"] = full_text  # Store full text for further processing
        
        # Parse location information using enhanced patterns
        location_info = VisitOpatijaTransformer.parse_location_from_text(full_text)
        data.update(location_info)
        
        # Extract location from text patterns
        location_patterns = [
            r"Lokacija:([^O]+?)(?=Organizator|$)",
            r"(?:u\s+|@\s+)([A-ZŠĐČĆŽ][^,\n]+?)(?=\s|$)",
            r"((?:Amadria\s+Park|Hotel\s+\w+|Villa\s+\w+|Park\s+\w+|Ljetna\s+pozornica)\s+[^,\n]{3,50})",
        ]
        for pattern in location_patterns:
            match = re.search(pattern, full_text)
            if match:
                location = match.group(1).strip()
                if location and len(location) > 2:
                    data["location"] = location
                    if "Opatija" not in location and any(v in location.lower() for v in ["amadria", "hotel", "villa", "park", "pozornica"]):
                        data["detected_address"] = f"{location}, Opatija"
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
                logger.info(f"Found {len(found)} events using selector: {sel}")
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


class VisitOpatijaPlaywrightScraper:
    """Playwright scraper for enhanced VisitOpatija.com detail page extraction."""

    async def fetch_event_details(self, page, event_url: str) -> Dict:
        """Fetch detailed address information from individual event page using Playwright."""
        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for content to load
            
            # Extract detailed location information from event detail page
            event_details = await page.evaluate("""
                () => {
                    const details = {};
                    
                    // Get full page text
                    const pageText = document.body.textContent;
                    details.full_text = pageText;
                    
                    // Look for Google Maps links (unique to Visit Opatija)
                    const mapLinks = document.querySelectorAll('a[href*="google.hr/maps/place"]');
                    if (mapLinks.length > 0) {
                        for (const link of mapLinks) {
                            const linkText = link.textContent.trim();
                            if (linkText && linkText.length > 3) {
                                details.detected_address = linkText + ', Opatija';
                                details.venue = linkText;
                                break;
                            }
                        }
                    }
                    
                    // Look for detailed address patterns in page content
                    if (!details.detected_address) {
                        const addressPatterns = [
                            // Full address with postal codes for Opatija region
                            /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?\\s*,?\\s*(?:51410|51414|51415|51417)\\s+(?:Opatija|Ika|Volosko|Veprinac))/gi,
                            // Street with number followed by Opatija
                            /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?)\\s*,?\\s*Opatija/gi,
                            // Opatija venues with detailed location
                            /((?:Amadria\\s+Park|Hotel\\s+\\w+|Villa\\s+\\w+|Park\\s+\\w+|Ljetna\\s+pozornica)\\s+[^,\\n]{3,50})(?:\\s*,?\\s*(?:u\\s+)?Opatija)?/gi
                        ];
                        
                        for (const pattern of addressPatterns) {
                            const matches = pageText.match(pattern);
                            if (matches && matches.length > 0) {
                                let address = matches[0].trim().replace(/\\s+/g, ' ');
                                if (!address.includes('Opatija')) {
                                    address += ', Opatija';
                                }
                                details.detected_address = address;
                                break;
                            }
                        }
                    }
                    
                    // Extract Opatija region city information
                    const cityMatch = pageText.match(/\\b(Opatija|Ika|Volosko|Veprinac|Lovran|Matulji|Mošćenička Draga)\\b/i);
                    if (cityMatch) {
                        details.city = cityMatch[1];
                    }
                    
                    // Extract venue information from structured content
                    if (!details.venue) {
                        const venueKeywords = ['Hotel', 'Villa', 'Park', 'Galerija', 'Muzej', 'Kazalište', 'Kino'];
                        for (const keyword of venueKeywords) {
                            const venuePattern = new RegExp(`(${keyword}\\\\s+[A-ZČĆĐŠŽ][a-zčćđšž\\\\s]*)`, 'i');
                            const venueMatch = pageText.match(venuePattern);
                            if (venueMatch) {
                                details.venue = venueMatch[1].trim();
                                break;
                            }
                        }
                    }
                    
                    return details;
                }
            """)
            
            return event_details
            
        except Exception as e:
            logger.error(f"Error fetching event details from {event_url}: {e}")
            return {}

    async def scrape_with_playwright(self, start_url: str = EVENTS_URL, max_pages: int = 5, fetch_details: bool = False) -> List[Dict]:
        """Scrape events using Playwright with enhanced address extraction."""
        try:
            from playwright.async_api import async_playwright
            
            all_events = []
            
            async with async_playwright() as p:
                # Configure browser
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
                    logger.info(f"Navigating to {start_url}")
                    await page.goto(start_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Handle cookie consent if present
                    try:
                        cookie_button = await page.query_selector('button:has-text("Prihvati"), button:has-text("Accept")')
                        if cookie_button:
                            await cookie_button.click()
                            await page.wait_for_timeout(1000)
                    except:
                        pass
                    
                    page_count = 0
                    current_url = start_url
                    
                    while current_url and page_count < max_pages:
                        page_count += 1
                        logger.info(f"Scraping page {page_count}...")
                        
                        if page_count > 1:
                            await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
                            await page.wait_for_timeout(3000)
                        
                        # Extract events from current page using enhanced selectors
                        events_data = await page.evaluate("""
                            () => {
                                const events = [];
                                
                                // Look for event elements using Visit Opatija specific patterns
                                const selectors = [
                                    'article.media-small.cnt-box',
                                    'article.cnt-box', 
                                    'article',
                                    'div.event',
                                    'div:has(a):has(img)'
                                ];
                                
                                let eventElements = [];
                                for (const selector of selectors) {
                                    const elements = document.querySelectorAll(selector);
                                    if (elements.length > 0) {
                                        eventElements = Array.from(elements);
                                        break;
                                    }
                                }
                                
                                eventElements.forEach((container, index) => {
                                    if (index >= 50) return; // Limit to prevent too many results
                                    
                                    const data = {};
                                    
                                    // Extract title
                                    const titleSelectors = ['h1', 'h2', 'h3', 'a', 'strong', '.title'];
                                    for (const selector of titleSelectors) {
                                        const titleEl = container.querySelector(selector);
                                        if (titleEl && titleEl.textContent.trim().length > 5) {
                                            data.title = titleEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    // Extract link
                                    const linkEl = container.querySelector('a');
                                    if (linkEl && linkEl.href) {
                                        data.link = linkEl.href;
                                    }
                                    
                                    // Extract image
                                    const imgEl = container.querySelector('img');
                                    if (imgEl && imgEl.src) {
                                        data.image = imgEl.src;
                                    }
                                    
                                    // Extract date
                                    const text = container.textContent;
                                    const dateMatch = text.match(/\\d{1,2}\\.\\d{1,2}\\.\\d{4}/);
                                    if (dateMatch) {
                                        data.date = dateMatch[0];
                                    }
                                    
                                    // Extract time
                                    const timeMatch = text.match(/\\d{1,2}:\\d{2}/);
                                    if (timeMatch) {
                                        data.time = timeMatch[0];
                                    }
                                    
                                    // Store full text for further processing
                                    data.full_text = text;
                                    
                                    // Only add if we have meaningful data
                                    if (data.title || data.link) {
                                        events.push(data);
                                    }
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
                            logger.info(f"Fetching detailed address info for {len(valid_events)} events...")
                            enhanced_events = []
                            
                            for i, event in enumerate(valid_events):
                                if event.get("link"):
                                    try:
                                        # Rate limiting - fetch details for every 3rd event
                                        if i % 3 == 0:
                                            details = await self.fetch_event_details(page, event["link"])
                                            if details:
                                                event.update(details)
                                                logger.info(f"Enhanced event {i+1}/{len(valid_events)}: {event.get('title', 'Unknown')}")
                                            
                                            await page.wait_for_timeout(1000)
                                        
                                        enhanced_events.append(event)
                                        
                                    except Exception as e:
                                        logger.error(f"Error fetching details for event {event.get('title', 'Unknown')}: {e}")
                                        enhanced_events.append(event)
                                else:
                                    enhanced_events.append(event)
                            
                            valid_events = enhanced_events
                        
                        all_events.extend(valid_events)
                        logger.info(f"Page {page_count}: Found {len(valid_events)} events (Total: {len(all_events)})")
                        
                        # Try to find next page link
                        next_url = None
                        try:
                            next_link = await page.query_selector('a[rel="next"], a.next, .pagination-next a, a.next')
                            if next_link:
                                next_href = await next_link.get_attribute('href')
                                if next_href and not next_href.startswith('#'):
                                    from urllib.parse import urljoin
                                    next_url = urljoin(current_url, next_href)
                        except:
                            pass
                        
                        current_url = next_url
                        
                        if not current_url:
                            logger.info("No more pages found")
                            break
                    
                except Exception as e:
                    logger.error(f"Error during scraping: {e}")
                
                await browser.close()
            
            return all_events
            
        except ImportError:
            logger.warning("Playwright not available, falling back to requests approach")
            return []
        except Exception as e:
            logger.error(f"Playwright error: {e}")
            return []


class VisitOpatijaScraper:
    """High level scraper for VisitOpatija.com."""

    def __init__(self) -> None:
        self.requests_scraper = VisitOpatijaRequestsScraper()
        self.playwright_scraper = VisitOpatijaPlaywrightScraper()
        self.transformer = VisitOpatijaTransformer()

    async def scrape_events(
        self, max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False
    ) -> List[EventCreate]:
        """Scrape events from VisitOpatija.com with optional detailed address fetching."""
        all_events: List[EventCreate] = []
        raw_events = []
        
        if use_playwright:
            # Try Playwright first for enhanced extraction
            logger.info("Using Playwright for enhanced VisitOpatija scraping...")
            try:
                raw_events = await self.playwright_scraper.scrape_with_playwright(
                    start_url=EVENTS_URL, 
                    max_pages=max_pages, 
                    fetch_details=fetch_details
                )
                logger.info(f"Playwright extracted {len(raw_events)} raw events")
            except Exception as e:
                logger.warning(f"Playwright failed: {e}, falling back to requests approach")
                raw_events = []
        
        # If Playwright fails or is disabled, use requests approach
        if not raw_events:
            logger.info("Using requests/BeautifulSoup approach...")
            try:
                raw_events = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
                
                # If fetch_details is enabled, enhance with detailed address info
                if fetch_details and raw_events:
                    logger.info("Fetching detailed address info for VisitOpatija events...")
                    enhanced_events = []
                    
                    for i, event in enumerate(raw_events):
                        if event.get("link") and i % 3 == 0:  # Rate limiting - every 3rd event
                            try:
                                details = await self.requests_scraper.fetch_event_details(event["link"])
                                if details:
                                    event.update(details)
                                    logger.info(f"Enhanced event {i+1}/{len(raw_events)}: {event.get('title', 'Unknown')}")
                                await asyncio.sleep(1)  # Rate limiting delay
                            except Exception as e:
                                logger.error(f"Error fetching details for event {event.get('title', 'Unknown')}: {e}")
                        
                        enhanced_events.append(event)
                    
                    raw_events = enhanced_events
                
                logger.info(f"Requests approach extracted {len(raw_events)} raw events")
            except Exception as e:
                logger.error(f"Requests approach also failed: {e}")
                raw_events = []
        
        # Transform raw data to EventCreate objects
        for raw_event in raw_events:
            event = await self.transformer.transform(raw_event)
            if event:
                all_events.append(event)
        
        await self.requests_scraper.close()
        
        logger.info(f"Transformed {len(all_events)} valid events from {len(raw_events)} raw events")
        return all_events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        """Insert events using individual Event creation and return number of new rows."""
        if not events:
            return 0

        from backend.app.core.database import SessionLocal
        from backend.app.models.event import Event
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
                        logger.debug(f"Skipping event {event_data.get('title', 'Unknown')}: {e}")
                        continue
                
                db.commit()
                return saved_count

            db.commit()
            return 0

        except Exception as e:
            logger.error(f"Error saving events to database: {e}")
            db.rollback()
            raise
        finally:
            db.close()


async def scrape_visitopatija_events(max_pages: int = 5, fetch_details: bool = False) -> Dict:
    """Scrape VisitOpatija.com events and save to database with optional detailed address fetching."""
    scraper = VisitOpatijaScraper()
    try:
        events = await scraper.scrape_events(
            max_pages=max_pages, 
            use_playwright=True, 
            fetch_details=fetch_details
        )
        saved = scraper.save_events_to_database(events)
        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved,
            "message": f"Successfully scraped {len(events)} events from VisitOpatija.com, saved {saved} new events" + 
                      (" (with detailed address info)" if fetch_details else ""),
        }
    except Exception as e:
        return {"status": "error", "message": f"VisitOpatija scraping failed: {e}"}
