"""VisitRijeka.hr events scraper with optional Bright Data proxy."""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from backend.app.models.schemas import EventCreate

# Import configuration
from backend.app.config.components import get_settings

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

# Configure logging
logger = logging.getLogger(__name__)

BASE_URL = "https://visitrijeka.hr"
EVENTS_URL = f"{BASE_URL}/en/events"



class VisitRijekaDataTransformer:
    """Transform raw VisitRijeka event data to :class:`EventCreate`."""

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
                        month_num = VisitRijekaDataTransformer.CRO_MONTHS.get(month.lower())
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
    def parse_location_from_text(text: str) -> Dict[str, str]:
        """Parse location information from event text using Rijeka-specific patterns."""
        result = {}
        
        if not text:
            return result
        
        # Pattern 1: Croatian address patterns for Rijeka region (51000 postal code)
        address_patterns = [
            # Full address with Rijeka postal code: "Sv. križ 33, 51000 Rijeka"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,?\s*51000\s+Rijeka)",
            # Street with number in Rijeka: "Korzo 15, Rijeka"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)\s*,?\s*Rijeka",
            # General Croatian address with number
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)",
            # Rijeka district patterns: "Trsat 5", "Korzo 12"
            r"((?:Trsat|Korzo|Delta|Centar)\s+\d+[a-z]?)"
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                detected_address = matches[0].strip()
                if "Rijeka" not in detected_address and "51000" not in detected_address:
                    detected_address += ", Rijeka"
                result["detected_address"] = detected_address
                break
        
        # Pattern 2: Extract Rijeka region cities and districts
        city_patterns = [
            r"\b(Rijeka|Trsat|Opatija|Crikvenica|Kastav|Matulji)\b"
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["city"] = match.group(1)
                break
        
        # Pattern 3: Extract Rijeka-specific venues
        venue_patterns = [
            # Theaters and cultural venues
            r"(HNK\s+Rijeka|Hrvatsko\s+narodno\s+kazalište\s+Ivan\s+Zajc)",
            r"(Muzej\s+grada\s+Rijeke|Prirodoslovno\s+muzej\s+Rijeka)",
            r"(Gradska\s+knjižnica\s+Rijeka|Biblioteka\s+Rijeka)",
            r"(Kino\s+Rijeka|Kino\s+[A-ZČĆĐŠŽ][a-zčćđšž]+)",
            r"(Galerija\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]*)",
            # Maritime and port venues
            r"(Luka\s+Rijeka|Port\s+of\s+Rijeka|Pomorski\s+muzej)",
            r"(Riva\s+Rijeka|Riječka\s+riva)",
            # Historic and landmark venues
            r"(Trsat\s+(?:Castle|Kastell?|Grad))",
            r"(Korzo|Glavna\s+šetnica)",
            # Modern venues
            r"(Hotel\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]*)",
            r"(Kongresni\s+centar|Convention\s+center)",
            r"(Astronomski\s+centar\s+Rijeka)",
            # Cultural centers
            r"(Dom\s+kulture|Kulturni\s+centar|Culture\s+center)"
        ]
        
        for pattern in venue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["venue"] = match.group(1).strip()
                break
        
        # Pattern 4: Extract location field patterns (for structured data)
        location_field_patterns = [
            r"Lokacija:\s*([^\n\r]+)",
            r"Location:\s*([^\n\r]+)",
            r"Venue:\s*([^\n\r]+)",
            r"Mjesto:\s*([^\n\r]+)"
        ]
        
        for pattern in location_field_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["venue_address"] = match.group(1).strip()
                break
        
        return result
    
    @staticmethod
    def extract_location(data: Dict) -> str:
        """Extract and format location with priority-based system for Rijeka region."""
        # Priority order: detected_address > venue_address > venue + city > location > city > venue (with Rijeka) > default
        
        # Highest priority: detected_address from detailed scraping
        if data.get("detected_address"):
            return data["detected_address"].strip()
        
        # Second priority: venue_address field (structured data)
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
        
        # Sixth priority: venue with Rijeka assumption (for known Rijeka venues)
        if venue:
            rijeka_venues = [
                "hnk", "kazalište", "muzej", "galerija", "kino", "biblioteka",
                "luka", "riva", "trsat", "korzo", "hotel", "kongresni", "astronomski",
                "dom kulture", "kulturni centar", "pomorski"
            ]
            if any(rv in venue.lower() for rv in rijeka_venues):
                return f"{venue}, Rijeka"
            return venue
        
        # Fallback
        return "Rijeka"

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
                name=name,
                time=parsed_time,
                date=parsed_date,
                location=location or "Rijeka",
                description=description or f"Event: {name}",
                price=price or "Check website",
                image=image,
                link=link,
            )
        except Exception:
            return None


class VisitRijekaRequestsScraper:
    """Scraper using httpx and BeautifulSoup with optional proxy."""

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(headers=HEADERS)

    async def fetch(self, url: str) -> httpx.Response:
        try:
            if USE_SB and USE_PROXY:
                params = {"url": url}
                async with httpx.AsyncClient(
                    headers=HEADERS, auth=(USER, PASSWORD), verify=False
                ) as client:
                    resp = await client.get(SCRAPING_BROWSER_EP, params=params, timeout=30)
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

    async def fetch_event_details(self, event_url: str) -> Dict:
        """Fetch detailed address information from individual event page."""
        try:
            resp = await self.fetch(event_url)
            soup = BeautifulSoup(resp.text, "html.parser")
            details = {}
            
            # Extract enhanced location information from event detail page
            page_text = soup.get_text()
            
            # Extract structured location fields
            location_selectors = [
                ".location", ".venue", ".place", ".address", 
                ".event-location", ".event-venue", ".event-place"
            ]
            
            for selector in location_selectors:
                location_el = soup.select_one(selector)
                if location_el:
                    details["venue_address"] = location_el.get_text(strip=True)
                    break
            
            # Look for JSON-LD structured data
            json_ld_scripts = soup.find_all("script", type="application/ld+json")
            for script in json_ld_scripts:
                try:
                    import json
                    structured_data = json.loads(script.string)
                    if isinstance(structured_data, dict):
                        # Extract location from Event schema
                        if structured_data.get("@type") == "Event":
                            location_data = structured_data.get("location", {})
                            if isinstance(location_data, dict):
                                address = location_data.get("address", {})
                                if isinstance(address, dict):
                                    street = address.get("streetAddress", "")
                                    city = address.get("addressLocality", "")
                                    postal = address.get("postalCode", "")
                                    if street and city:
                                        full_address = f"{street}, {postal} {city}" if postal else f"{street}, {city}"
                                        details["detected_address"] = full_address.strip()
                                elif isinstance(address, str):
                                    details["detected_address"] = address
                                
                                venue_name = location_data.get("name")
                                if venue_name:
                                    details["venue"] = venue_name
                except (json.JSONDecodeError, AttributeError):
                    continue
            
            # Look for detailed address patterns in page content
            address_patterns = [
                # Rijeka postal code patterns
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,?\s*51000\s+Rijeka)",
                # Street + Rijeka patterns
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)\s*,?\s*Rijeka",
                # General Croatian address with number
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)",
                # Rijeka district patterns
                r"((?:Trsat|Korzo|Delta|Centar)\s+\d+[a-z]?)"
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    for match in matches:
                        match = match.strip()
                        # Validate it looks like a real address
                        if re.search(r"[A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+", match):
                            if "Rijeka" not in match and "51000" not in match:
                                match += ", Rijeka"
                            details["detected_address"] = match
                            break
                    if details.get("detected_address"):
                        break
            
            # Extract Rijeka-specific venue information
            rijeka_venues = [
                "HNK Rijeka", "Hrvatsko narodno kazalište Ivan Zajc", "Muzej grada Rijeke",
                "Prirodoslovno muzej Rijeka", "Gradska knjižnica Rijeka", "Astronomski centar Rijeka",
                "Luka Rijeka", "Port of Rijeka", "Pomorski muzej", "Riva Rijeka",
                "Trsat Castle", "Trsat Kastell", "Korzo", "Glavna šetnica",
                "Dom kulture", "Kulturni centar", "Kongresni centar"
            ]
            
            for venue in rijeka_venues:
                if venue in page_text and not details.get("venue"):
                    details["venue"] = venue
                    break
            
            # Ensure Rijeka is recognized as city
            if "Rijeka" in page_text and not details.get("city"):
                details["city"] = "Rijeka"
            
            # Store full page text for further processing
            details["full_text"] = page_text
            
            return details
            
        except Exception as e:
            logger.error(f"Error fetching event details from {event_url}: {e}")
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
            description = desc_el.get_text(separator=" ", strip=True)
            data["description"] = description
            
            # Parse location information from description using class method
            location_info = VisitRijekaDataTransformer.parse_location_from_text(description)
            data.update(location_info)

        date_el = soup.find(string=re.compile(r"\d{4}"))
        if date_el:
            data["date"] = date_el.strip()

        time_el = soup.find(string=re.compile(r"\d{1,2}:\d{2}"))
        if time_el:
            data["time"] = time_el.strip()

        img_el = soup.select_one("img[src]")
        if img_el:
            data["image"] = img_el.get("src")

        # Enhanced location extraction with multiple selectors
        location_selectors = [".location", ".venue", ".place", ".address", ".event-location"]
        for selector in location_selectors:
            loc_el = soup.select_one(selector)
            if loc_el:
                location_text = loc_el.get_text(strip=True)
                data["location"] = location_text
                
                # Parse additional location patterns from the found element
                additional_info = VisitRijekaDataTransformer.parse_location_from_text(location_text)
                data.update(additional_info)
                break

        price_el = soup.select_one(".price")
        if price_el:
            data["price"] = price_el.get_text(strip=True)
        
        # Extract full page text for comprehensive location parsing
        page_text = soup.get_text()
        data["full_text"] = page_text
        
        # Apply comprehensive address pattern detection to full page
        if not data.get("detected_address") and not data.get("venue"):
            page_location_info = VisitRijekaDataTransformer.parse_location_from_text(page_text)
            # Only add if we don't already have better location info
            for key, value in page_location_info.items():
                if not data.get(key):
                    data[key] = value

        return data

    def parse_listing_element(self, el: Tag) -> Dict:
        data: Dict[str, str] = {}
        link_el = el.select_one("a")
        if link_el and link_el.get("href"):
            data["link"] = urljoin(BASE_URL, link_el.get("href"))
            if link_el.get_text(strip=True):
                data["title"] = link_el.get_text(strip=True)

        date_el = el.select_one(".date, time")
        if date_el and date_el.get_text(strip=True):
            data["date"] = date_el.get_text(strip=True)

        img_el = el.select_one("img")
        if img_el and img_el.get("src"):
            data["image"] = img_el.get("src")

        loc_el = el.select_one(".location, .venue, .place")
        if loc_el:
            data["location"] = loc_el.get_text(strip=True)

        price_el = el.select_one(".price")
        if price_el:
            data["price"] = price_el.get_text(strip=True)

        return data

    async def scrape_events_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        resp = await self.fetch(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        events: List[Dict] = []
        containers = []
        selectors = ["li.event-item", "div.event-item", "article", ".events-list li"]
        for sel in selectors:
            found = soup.select(sel)
            if found:
                containers = found
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


class VisitRijekaPlaywrightScraper:
    """Playwright scraper for enhanced VisitRijeka event and address extraction."""

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
                    
                    // Look for JSON-LD structured data
                    const jsonLdScripts = document.querySelectorAll('script[type="application/ld+json"]');
                    for (const script of jsonLdScripts) {
                        try {
                            const structuredData = JSON.parse(script.textContent);
                            if (structuredData['@type'] === 'Event') {
                                const location = structuredData.location;
                                if (location) {
                                    if (location.name) {
                                        details.venue = location.name;
                                    }
                                    if (location.address) {
                                        if (typeof location.address === 'object') {
                                            const street = location.address.streetAddress || '';
                                            const city = location.address.addressLocality || '';
                                            const postal = location.address.postalCode || '';
                                            if (street && city) {
                                                details.detected_address = postal ? 
                                                    `${street}, ${postal} ${city}` : 
                                                    `${street}, ${city}`;
                                            }
                                        } else if (typeof location.address === 'string') {
                                            details.detected_address = location.address;
                                        }
                                    }
                                }
                            }
                        } catch (e) {
                            // Ignore JSON parsing errors
                        }
                    }
                    
                    // Look for address patterns in page content
                    const addressPatterns = [
                        // Rijeka postal code patterns: "Sv. križ 33, 51000 Rijeka"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?\\s*,?\\s*51000\\s+Rijeka)/gi,
                        // Street + Rijeka patterns: "Korzo 15, Rijeka"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?)\\s*,?\\s*Rijeka/gi,
                        // General Croatian address with number
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?)/gi,
                        // Rijeka district patterns: "Trsat 5", "Korzo 12"
                        /((?:Trsat|Korzo|Delta|Centar)\\s+\\d+[a-z]?)/gi
                    ];
                    
                    if (!details.detected_address) {
                        for (const pattern of addressPatterns) {
                            const matches = [...pageText.matchAll(pattern)];
                            if (matches.length > 0) {
                                for (const match of matches) {
                                    let address = match[1].trim();
                                    // Validate it looks like a real address
                                    if (/[A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+/.test(address)) {
                                        if (!address.includes('Rijeka') && !address.includes('51000')) {
                                            address += ', Rijeka';
                                        }
                                        details.detected_address = address;
                                        break;
                                    }
                                }
                                if (details.detected_address) break;
                            }
                        }
                    }
                    
                    // Look for Rijeka-specific venues
                    const rijekaVenues = [
                        'HNK Rijeka', 'Hrvatsko narodno kazalište Ivan Zajc', 'Muzej grada Rijeke',
                        'Prirodoslovno muzej Rijeka', 'Gradska knjižnica Rijeka', 'Astronomski centar Rijeka',
                        'Luka Rijeka', 'Port of Rijeka', 'Pomorski muzej', 'Riva Rijeka',
                        'Trsat Castle', 'Trsat Kastell', 'Korzo', 'Glavna šetnica',
                        'Dom kulture', 'Kulturni centar', 'Kongresni centar'
                    ];
                    
                    if (!details.venue) {
                        for (const venue of rijekaVenues) {
                            if (pageText.includes(venue)) {
                                details.venue = venue;
                                break;
                            }
                        }
                    }
                    
                    // Ensure Rijeka is recognized as city
                    if (pageText.includes('Rijeka')) {
                        details.city = 'Rijeka';
                    }
                    
                    // Store full page text for further processing
                    details.full_text = pageText;
                    
                    return details;
                }
            """)
            
            return event_details
            
        except Exception as e:
            logger.error(f"Error fetching event details from {event_url}: {e}")
            return {}

    async def scrape_with_playwright(self, start_url: str = None, max_pages: int = 5, fetch_details: bool = False) -> List[Dict]:
        """Scrape events using Playwright with enhanced address extraction."""
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
                    # Start with events page
                    base_url = start_url or EVENTS_URL
                    logger.info(f"Navigating to {base_url}")
                    await page.goto(base_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Handle cookie consent if present
                    try:
                        cookie_selectors = [
                            'button[id*="accept"]', 'button[class*="accept"]',
                            'button:has-text("Accept")', 'button:has-text("Prihvati")',
                            '.cookie-accept', '#cookie-accept'
                        ]
                        for selector in cookie_selectors:
                            cookie_button = await page.query_selector(selector)
                            if cookie_button:
                                await cookie_button.click()
                                await page.wait_for_timeout(1000)
                                break
                    except:
                        pass
                    
                    page_count = 0
                    current_url = base_url
                    
                    while current_url and page_count < max_pages:
                        page_count += 1
                        logger.info(f"Scraping page {page_count}...")
                        
                        if page_count > 1:
                            await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
                            await page.wait_for_timeout(3000)
                        
                        # Extract events from current page
                        events_data = await page.evaluate("""
                            () => {
                                const events = [];
                                
                                // Look for event containers with multiple selectors
                                const selectors = [
                                    'li.event-item', 'div.event-item', 'article',
                                    '.events-list li', '.event-listing .event',
                                    '[class*="event"]', '.post', '.entry'
                                ];
                                
                                let eventElements = [];
                                for (const selector of selectors) {
                                    const elements = document.querySelectorAll(selector);
                                    if (elements.length > 0) {
                                        eventElements = [...elements];
                                        break;
                                    }
                                }
                                
                                eventElements.forEach((container, index) => {
                                    if (index >= 20) return; // Limit to prevent too many results
                                    
                                    const data = {};
                                    
                                    // Extract title and link
                                    const linkEl = container.querySelector('a');
                                    if (linkEl) {
                                        data.title = linkEl.textContent.trim();
                                        data.link = linkEl.href;
                                    }
                                    
                                    // Extract date
                                    const dateSelectors = ['.date', 'time', '.event-date', '[class*="date"]'];
                                    for (const selector of dateSelectors) {
                                        const dateEl = container.querySelector(selector);
                                        if (dateEl && dateEl.textContent.trim()) {
                                            data.date = dateEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    // Extract image
                                    const imgEl = container.querySelector('img');
                                    if (imgEl && imgEl.src) {
                                        data.image = imgEl.src;
                                    }
                                    
                                    // Extract location from various elements
                                    const locationSelectors = ['.location', '.venue', '.place', '.address'];
                                    for (const selector of locationSelectors) {
                                        const locEl = container.querySelector(selector);
                                        if (locEl) {
                                            data.location = locEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    // Extract price
                                    const priceEl = container.querySelector('.price');
                                    if (priceEl) {
                                        data.price = priceEl.textContent.trim();
                                    }
                                    
                                    // Store container text for location parsing
                                    data.full_text = container.textContent;
                                    
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
                                                # Merge detailed information
                                                event.update(details)
                                                logger.info(f"Enhanced event {i+1}/{len(valid_events)}: {event.get('title', 'Unknown')}")
                                            
                                            # Add delay between detail fetches
                                            await page.wait_for_timeout(1500)
                                        
                                        enhanced_events.append(event)
                                        
                                    except Exception as e:
                                        logger.error(f"Error fetching details for event {event.get('title', 'Unknown')}: {e}")
                                        enhanced_events.append(event)  # Add original event even if detail fetch fails
                                else:
                                    enhanced_events.append(event)
                            
                            valid_events = enhanced_events
                        
                        all_events.extend(valid_events)
                        logger.info(f"Page {page_count}: Found {len(valid_events)} events (Total: {len(all_events)})")
                        
                        # Try to find next page link
                        next_url = None
                        try:
                            next_selectors = [
                                'a[rel="next"]', '.pagination-next a', 'a.next',
                                'a:has-text("Next")', 'a:has-text("Sljedeća")',
                                '.pagination a:last-child'
                            ]
                            for selector in next_selectors:
                                next_link = await page.query_selector(selector)
                                if next_link:
                                    next_href = await next_link.get_attribute('href')
                                    if next_href and not next_href.startswith('#'):
                                        next_url = urljoin(current_url, next_href)
                                        break
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


class VisitRijekaScraper:
    """High level scraper for VisitRijeka.hr."""

    def __init__(self) -> None:
        self.requests_scraper = VisitRijekaRequestsScraper()
        self.playwright_scraper = VisitRijekaPlaywrightScraper()
        self.transformer = VisitRijekaDataTransformer()

    async def scrape_events(self, max_pages: int = 5, use_playwright: bool = True, 
                          fetch_details: bool = False) -> List[EventCreate]:
        """Scrape events from VisitRijeka with optional enhanced address extraction."""
        all_events: List[EventCreate] = []
        raw_events = []
        
        if use_playwright:
            # Try Playwright first for enhanced extraction
            logger.info("Using Playwright for enhanced VisitRijeka scraping...")
            try:
                raw_events = await self.playwright_scraper.scrape_with_playwright(
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
                
                # Enhance with detail fetching if requested
                if fetch_details and raw_events:
                    logger.info(f"Fetching detailed address info for {len(raw_events)} events...")
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
                                        logger.info(f"Enhanced event {i+1}/{len(raw_events)}: {event.get('title', 'Unknown')}")
                                    
                                    # Add delay between detail fetches
                                    await asyncio.sleep(1)
                                
                                enhanced_events.append(event)
                                
                            except Exception as e:
                                logger.error(f"Error fetching details for event {event.get('title', 'Unknown')}: {e}")
                                enhanced_events.append(event)  # Add original event even if detail fetch fails
                        else:
                            enhanced_events.append(event)
                    
                    raw_events = enhanced_events
                
                logger.info(f"Requests approach extracted {len(raw_events)} raw events")
            except Exception as e:
                logger.error(f"Requests approach also failed: {e}")
                raw_events = []
        
        # Transform raw data to EventCreate objects
        for raw_event in raw_events:
            event = self.transformer.transform(raw_event)
            if event:
                all_events.append(event)
        
        await self.requests_scraper.close()
        logger.info(f"Transformed {len(all_events)} valid events from {len(raw_events)} raw events")
        return all_events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        from sqlalchemy import select, tuple_
        from sqlalchemy.dialects.postgresql import insert

        from backend.app.core.database import SessionLocal
        from backend.app.models.event import Event

        if not events:
            return 0

        db = SessionLocal()
        try:
            event_dicts = [e.model_dump() for e in events]
            pairs = [(e["name"], e["date"]) for e in event_dicts]
            existing = db.execute(
                select(Event.name, Event.date).where(tuple_(Event.name, Event.date).in_(pairs))
            ).all()
            existing_pairs = set(existing)
            to_insert = [e for e in event_dicts if (e["name"], e["date"]) not in existing_pairs]
            if to_insert:
                stmt = insert(Event).values(to_insert)
                stmt = stmt.on_conflict_do_nothing(index_elements=["name", "date"])
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


async def scrape_visitrijeka_events(max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> Dict:
    scraper = VisitRijekaScraper()
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
            "message": f"Scraped {len(events)} events from VisitRijeka.hr, saved {saved} new events" + 
                      (" (with enhanced address extraction)" if fetch_details else ""),
        }
    except Exception as e:
        return {"status": "error", "message": f"VisitRijeka scraping failed: {e}"}
