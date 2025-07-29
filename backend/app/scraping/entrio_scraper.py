"""
Entrio.hr event scraper integrated with the backend database.
Combines both BrightData proxy and Playwright approaches.
"""

import asyncio
import json
import os
import re
import time
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlparse

import httpx
import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from sqlalchemy import select, tuple_
from sqlalchemy.dialects.postgresql import insert

from ..core.config import settings
from ..core.database import SessionLocal
# Temporarily disabled until OpenAI dependency is added
# from ..core.llm_location_service import llm_location_service
from ..models.event import Event
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
BRD_WSS = f"wss://{USER}:{PASSWORD}@brd.superproxy.io:9222"

CATEGORY_URL = "https://www.entrio.hr/hr/"
USE_SB = _scraping_config.use_scraping_browser
USE_PROXY = _scraping_config.use_proxy
USE_PLAYWRIGHT = _scraping_config.use_playwright

HEADERS = _scraping_config.headers_dict


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
    async def extract_location_with_llm(title: str, description: str = "", context: str = "") -> Optional[str]:
        """Extract location using LLM as fallback when basic extraction fails."""
        # Temporarily disabled until OpenAI dependency is added
        return None
        
        # if not llm_location_service.is_enabled():
        #     return None
        #     
        # try:
        #     result = await llm_location_service.extract_location(title, description, context)
        #     if result and result.confidence > 0.6:  # Only use high-confidence results
        #         return result.full_location
        # except Exception as e:
        #     print(f"LLM location extraction error: {e}")
        
        # return None

    @staticmethod
    def extract_location_from_text(title: str, description: str = "") -> str:
        """Extract location from event title and description."""
        text = f"{title} {description}".lower()
        
        # Known Croatian cities and venues in order of specificity
        croatian_locations = [
            # Specific venues first
            ("poljud", "Split"),
            ("arena pula", "Pula"),
            ("pula arena", "Pula"),
            ("amfiteatar pula", "Pula"),
            ("rimsko kazalište", "Pula"),
            ("malo rimsko kazalište", "Pula"),
            ("jarun", "Zagreb"),
            ("maksimir", "Zagreb"),
            ("dom sportova", "Zagreb"),
            ("arena zagreb", "Zagreb"),
            ("hipodrom sinj", "Sinj"),
            ("ljetno kino makarska", "Makarska"),
            ("summer cinema makarska", "Makarska"),
            ("opatija", "Opatija"),
            ("amadria park", "Opatija"),
            
            # Cities
            ("split", "Split"),
            ("pula", "Pula"),
            ("rijeka", "Rijeka"),
            ("zadar", "Zadar"),
            ("dubrovnik", "Dubrovnik"),
            ("osijek", "Osijek"),
            ("sisak", "Sisak"),
            ("karlovac", "Karlovac"),
            ("varaždin", "Varaždin"),
            ("sinj", "Sinj"),
            ("makarska", "Makarska"),
            ("trogir", "Trogir"),
            ("hvar", "Hvar"),
            ("korčula", "Korčula"),
            ("rovinj", "Rovinj"),
            ("poreč", "Poreč"),
            ("umag", "Umag"),
            ("krk", "Krk"),
            ("crikvenica", "Crikvenica"),
            ("senj", "Senj"),
            ("gospić", "Gospić"),
            ("metković", "Metković"),
            ("ploče", "Ploče"),
            ("otočac", "Otočac"),
            ("samobor", "Samobor"),
            ("velika gorica", "Velika Gorica"),
            ("zaprešić", "Zaprešić"),
            # Zagreb should be last as it's too common
            ("zagreb", "Zagreb"),
        ]
        
        # Search for location mentions
        for keyword, city in croatian_locations:
            if keyword in text:
                return city
        
        # If no specific location found, return None to skip event
        return None

    @staticmethod
    def extract_location_from_enhanced_data(scraped_data: Dict) -> str:
        """Extract and format location from enhanced scraped data with address support."""
        parts = []
        
        # Handle enhanced address data from detailed scraping
        # Priority order: detected_address > street_address > venue > city > region
        if scraped_data.get("detected_address"):
            return scraped_data["detected_address"]
        
        if scraped_data.get("street_address"):
            parts.append(scraped_data["street_address"])
        elif scraped_data.get("venue") or scraped_data.get("venue_detail"):
            venue = scraped_data.get("venue_detail") or scraped_data.get("venue")
            parts.append(venue)
        
        # Add city information
        city = scraped_data.get("city") or scraped_data.get("city_name")
        if city:
            parts.append(city)
        
        # If we have enhanced location data, use it
        if scraped_data.get("full_location") and not parts:
            # Try to extract location from full location text
            location = EventDataTransformer.extract_location_from_text(scraped_data["full_location"], "")
            if location:
                return location
            # If no specific city found, use full location as fallback
            return scraped_data["full_location"]
        
        if parts:
            # Clean and deduplicate parts
            unique_parts = []
            for part in parts:
                part_clean = str(part).strip()
                if part_clean and part_clean not in unique_parts:
                    unique_parts.append(part_clean)
            return ", ".join(unique_parts)
        
        # Fallback to standard location extraction
        title = scraped_data.get("title", "")
        description = scraped_data.get("description", "")
        venue = scraped_data.get("venue", "")
        
        # Try to extract from any available text
        location = EventDataTransformer.extract_location_from_text(f"{title} {description} {venue}", "")
        return location

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
    async def transform_to_event_create(scraped_data: Dict) -> Optional[EventCreate]:
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
                # Use default date for events without dates (upcoming events)
                from datetime import date, timedelta
                parsed_date = date.today() + timedelta(days=7)  # Default to next week

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

            # Try to extract title from URL if name is empty
            if not name or len(name) < 3:
                link = scraped_data.get("link", "")
                if link:
                    # Extract event name from URL (e.g., "jim-jefferies-live-in-zagreb" from URL)
                    import re
                    url_match = re.search(r'/event/([^/?]+)', link)
                    if url_match:
                        url_name = url_match.group(1)
                        # Clean up the URL name
                        name = url_name.replace('-', ' ').replace('_', ' ')
                        # Remove numbers at the end (like "25641")
                        name = re.sub(r'\s+\d+$', '', name)
                        # Capitalize words
                        name = ' '.join(word.capitalize() for word in name.split())
                        
            # Final validation
            if not name or len(name) < 3:
                return None

            # Try to extract location using enhanced data if not found
            if not location:
                location = EventDataTransformer.extract_location_from_enhanced_data(scraped_data)
            
            # Fallback to basic extraction if enhanced extraction failed
            if not location:
                location = EventDataTransformer.extract_location_from_text(name, description)
            
            # Try LLM fallback if basic extraction failed
            if not location:
                venue_context = scraped_data.get("venue", "")
                location = await EventDataTransformer.extract_location_with_llm(
                    name, description, venue_context
                )
                if location:
                    print(f"LLM extracted location for '{name}': {location}")
            
            # Skip event if we still can't determine location
            if not location:
                print(f"Skipping event '{name}' - could not determine location")
                return None

            return EventCreate(
                title=name,
                time=parsed_time,
                date=parsed_date,
                location=location,
                description=description or f"Event: {name}",
                price=price or "Contact organizer",
                image=image_url,
                link=link,
                source="entrio",
                tags=[]  # Initialize tags as empty list to avoid ARRAY type issues
            )

        except Exception as e:
            print(f"Error transforming event data: {e}")
            return None


class EntrioRequestsScraper:
    """Scraper using requests and BeautifulSoup."""

    def __init__(self):
        self.session = requests.Session()

    async def fetch_async(self, url: str) -> httpx.Response:
        """Asynchronously fetch URL with proxy support."""
        try:
            if USE_SB and USE_PROXY:
                params = {"url": url}
                async with httpx.AsyncClient(
                    headers=HEADERS,
                    auth=(USER, PASSWORD),
                    verify=False,
                ) as client:
                    resp = await client.get(
                        SCRAPING_BROWSER_EP,
                        params=params,
                        timeout=30,
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
            print(f"[ERROR] Request failed for {url}: {e}")
            raise

    def fetch(self, url: str) -> requests.Response:
        """Fetch URL with proxy support."""
        try:
            if USE_SB and USE_PROXY:
                params = {"url": url}
                resp = self.session.get(
                    SCRAPING_BROWSER_EP,
                    params=params,
                    headers=HEADERS,
                    auth=(USER, PASSWORD),
                    timeout=30,
                    verify=False,
                )
            elif USE_PROXY:
                resp = self.session.get(
                    url,
                    headers=HEADERS,
                    proxies={"http": PROXY, "https": PROXY},
                    timeout=30,
                    verify=False,
                )
            else:
                resp = self.session.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            return resp
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed for {url}: {e}")
            raise

    def extract_location_from_event_page(self, event_url: str) -> Dict:
        """Extract detailed location information from event detail page using real Entrio.hr selectors."""
        try:
            response = self.fetch(event_url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            location_data = {}
            
            # Primary selector - discovered through MCP investigation
            location_header = soup.select_one('.event-header__location')
            if location_header:
                location_text = location_header.get_text(strip=True)
                if location_text:
                    location_data['full_location'] = location_text
                    
                    # Parse "Venue Name, City" format from event detail pages
                    venue_city_parts = location_text.split(',')
                    if len(venue_city_parts) >= 2:
                        location_data['venue'] = venue_city_parts[0].strip()
                        location_data['city'] = venue_city_parts[1].strip()
                        location_data['location'] = location_text  # "Venue Name, City"
                    else:
                        location_data['location'] = location_text
                        location_data['venue'] = location_text
            
            # Fallback selectors if primary selector doesn't work
            if not location_data.get('full_location'):
                fallback_selectors = [
                    # Common location indicators
                    ".event-location",
                    ".location", 
                    ".venue",
                    ".address",
                    '[class*="location"]',
                    '[class*="venue"]',
                    '[class*="address"]',
                    '[class*="adresa"]',
                    '[class*="lokacija"]',
                    '.venue-info',
                    '.location-details'
                ]
                
                for selector in fallback_selectors:
                    elements = soup.select(selector)
                    for element in elements:
                        text = element.get_text(strip=True) if hasattr(element, 'get_text') else str(element)
                        if text and len(text) > 3:
                            # Store the full location text
                            if not location_data.get('full_location') or len(text) > len(location_data.get('full_location', '')):
                                location_data['full_location'] = text
                                location_data['location'] = text
                        
                        # Try to extract specific venue information
                        venue_selectors = ['.venue', '.venue-name', '[class*="venue"]', '.hall', '[class*="hall"]', '.dvorana']
                        for venue_sel in venue_selectors:
                            venue_el = element.select_one(venue_sel)
                            if venue_el:
                                venue_text = venue_el.get_text(strip=True)
                                if venue_text:
                                    location_data['venue'] = venue_text
                        
                        # Try to extract city information from links
                        city_links = element.select('a[href*="grad"], a[href*="city"], a[href*="location"]')
                        for city_link in city_links:
                            city_text = city_link.get_text(strip=True)
                            if city_text:
                                location_data['city'] = city_text
                                location_data['city_url'] = city_link.get('href', '')
                        
                        # Croatian address pattern detection
                        import re
                        address_patterns = [
                            r'([A-ZČĆĐŠŽ][a-zčćđšž\s]+(?:ulica|cesta|trg|put|avenija|bb)\s*\d*[a-z]?)',
                            r'(\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)',
                            r'([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,\s*\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)'
                        ]
                        
                        for pattern in address_patterns:
                            matches = re.findall(pattern, text, re.IGNORECASE)
                            if matches:
                                location_data['street_address'] = matches[0].strip()
                                break
            
            # Look for location in the page title or meta description if not found
            if not location_data:
                title = soup.find('title')
                if title:
                    title_text = title.get_text(strip=True)
                    location_data['full_location'] = title_text
                
                # Look in meta description
                meta_desc = soup.find('meta', attrs={'name': 'description'})
                if meta_desc and meta_desc.get('content'):
                    if not location_data.get('full_location'):
                        location_data['full_location'] = meta_desc['content']
            
            return location_data
                    
        except Exception as e:
            print(f"Error extracting location from event page {event_url}: {e}")
        
        return {}

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
        resp = await self.fetch_async(url)
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
                    # Try to extract detailed location data if we have a link
                    if event_data.get("link"):
                        detailed_location_data = self.extract_location_from_event_page(event_data["link"])
                        if detailed_location_data:
                            # Merge the detailed location data
                            event_data.update(detailed_location_data)
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
        all_events = []
        current_url = start_url
        page_count = 0

        while current_url and page_count < max_pages:
            try:
                events, next_url = await self.scrape_events_page(current_url)
                all_events.extend(events)

                page_count += 1
                print(
                    f"Page {page_count}: Found {len(events)} events (Total: {len(all_events)})"
                )

                if not events:
                    break

                current_url = next_url
                await asyncio.sleep(1)  # Be respectful

            except Exception as e:
                print(f"Failed to scrape page {current_url}: {e}")
                break

        return all_events


class EntrioPlaywrightScraper:
    """Scraper using Playwright for JavaScript-heavy pages."""

    async def scrape_with_playwright(
        self, start_url: str = "https://entrio.hr/", max_pages: int = 5, fetch_details: bool = False
    ) -> List[Dict]:
        """Scrape events using Playwright with anti-detection."""
        from playwright.async_api import async_playwright
        import random

        all_events = []
        
        # Better user agents
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
        ]

        async with async_playwright() as p:
            # Launch with maximum anti-detection
            if USE_PROXY:
                browser = await p.chromium.connect_over_cdp(BRD_WSS)
            else:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--disable-field-trial-config',
                        '--disable-back-forward-cache',
                        '--disable-ipc-flooding-protection',
                        '--no-first-run',
                        '--no-default-browser-check',
                        '--no-pings',
                        '--password-store=basic',
                        '--use-mock-keychain'
                    ]
                )

            # Create realistic browser context
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent=random.choice(user_agents),
                locale='hr-HR',
                timezone_id='Europe/Zagreb',
                geolocation={'latitude': 45.8150, 'longitude': 15.9819},  # Zagreb coordinates
                permissions=['geolocation'],
                extra_http_headers={
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                    'Accept-Language': 'hr-HR,hr;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1'
                }
            )
            
            page = await context.new_page()
            
            # Add stealth script
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });
            """)

            # Try to access the main page first 
            try:
                print(f"→ Fetching {start_url}")
                await page.goto(start_url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                # Extract events from homepage first
                homepage_events = await page.evaluate("""
                    () => {
                        const events = [];
                        const eventLinks = Array.from(document.querySelectorAll('a[href]'))
                            .filter(link => link.href.includes('/event/') && !link.href.includes('my_event'))
                            .slice(0, 20);
                        
                        eventLinks.forEach(linkEl => {
                            const data = {};
                            data.link = linkEl.href;
                            data.title = linkEl.textContent?.trim() || linkEl.getAttribute('title') || '';
                            
                            const imgEl = linkEl.querySelector('img');
                            if (imgEl && imgEl.src) {
                                data.image_url = imgEl.src;
                            }
                            
                            events.push(data);
                        });
                        
                        return events;
                    }
                """)
                
                print(f"Found {len(homepage_events)} events on homepage")
                all_events.extend(homepage_events)
                
                # Now try to access events page with advanced Cloudflare bypass
                await self.access_events_page_with_bypass(page, all_events, max_pages)

                print(f"Total events found: {len(all_events)}")
                
                if not all_events:
                    print("No events found on any page")
                    
            except Exception as e:
                print(f"Failed to scrape page {start_url}: {e}")

            await browser.close()

        return all_events

    async def access_events_page_with_bypass(self, page, all_events, max_pages):
        """Advanced Cloudflare bypass to access events page."""
        import random
        
        print("Attempting to access events page with advanced bypass...")
        
        # Method 1: Handle cookie acceptance and human simulation
        try:
            print("Step 1: Handling cookie acceptance and overlays...")
            
            # Look for and handle cookie acceptance
            await self.handle_cookie_acceptance(page)
            
            # Advanced human simulation
            await self.simulate_human_behavior(page)
            
            # Wait and try to find events link
            await page.wait_for_timeout(2000)
            
            # Try multiple selectors for events link
            events_selectors = [
                'a[href*="/events"]:not([href*="my_events"])',
                'a[href="/events"]',
                'a[href="https://www.entrio.hr/events"]',
                'a:text("Događaji")',
                'a:text("Events")',
                'a:text("Svi događaji")',
                'nav a[href*="events"]'
            ]
            
            events_link = None
            for selector in events_selectors:
                try:
                    events_link = await page.query_selector(selector)
                    if events_link:
                        print(f"Found events link with selector: {selector}")
                        break
                except:
                    continue
            
            if events_link:
                print("Attempting natural click on events link...")
                
                # Scroll to element smoothly
                await events_link.scroll_into_view_if_needed()
                await page.wait_for_timeout(1000)
                
                # Try clicking with force if needed
                try:
                    await events_link.click(force=True)
                    await page.wait_for_timeout(8000)  # Wait longer for page load
                    
                    page_title = await page.title()
                    page_url = page.url
                    print(f"After click - URL: {page_url}, Title: {page_title}")
                    
                    if "/events" in page_url and "Cloudflare" not in page_title and "Attention Required" not in page_title:
                        print(f"✅ Successfully accessed events page: {page_title}")
                        await self.extract_events_from_current_page(page, all_events, max_pages, fetch_details=fetch_details)
                        return
                    else:
                        print("⚠️ Events page click was blocked or redirected")
                        
                except Exception as click_error:
                    print(f"Click failed: {click_error}")
            
        except Exception as e:
            print(f"Method 1 failed: {e}")

    async def handle_cookie_acceptance(self, page):
        """Handle cookie acceptance overlays and popups."""
        try:
            # Wait a bit for any overlays to appear
            await page.wait_for_timeout(2000)
            
            # Look for cookie acceptance buttons/overlays
            cookie_selectors = [
                '.accept__overlay',
                '.js-accept-overlay',
                '.cookie-accept',
                '.cookie-consent button',
                'button:text("Accept")',
                'button:text("Prihvati")',
                'button:text("OK")',
                '.accept-cookies',
                '[class*="cookie"] button',
                '[class*="accept"] button'
            ]
            
            for selector in cookie_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        print(f"Found cookie element: {selector}")
                        # Try to remove overlay or click accept
                        if 'overlay' in selector:
                            await page.evaluate(f'document.querySelector("{selector}")?.remove()')
                        else:
                            await element.click()
                        await page.wait_for_timeout(1000)
                        print(f"Handled cookie element: {selector}")
                        break
                except:
                    continue
                    
        except Exception as e:
            print(f"Cookie handling failed: {e}")

    async def simulate_human_behavior(self, page):
        """Simulate realistic human browsing behavior."""
        import random
        
        try:
            # Simulate realistic mouse movements
            for _ in range(3):
                x = random.randint(100, 1000)
                y = random.randint(100, 600)
                await page.mouse.move(x, y)
                await page.wait_for_timeout(random.randint(200, 800))
            
            # Simulate scrolling
            await page.evaluate("""
                () => {
                    const scrollAmount = Math.random() * 500 + 200;
                    window.scrollTo({
                        top: scrollAmount,
                        behavior: 'smooth'
                    });
                }
            """)
            
            await page.wait_for_timeout(random.randint(1000, 3000))
            
            # Scroll back up
            await page.evaluate("window.scrollTo({ top: 0, behavior: 'smooth' })")
            await page.wait_for_timeout(random.randint(1000, 2000))
            
        except Exception as e:
            print(f"Human simulation failed: {e}")
        
        # Method 2: Enhanced direct URL bypass with stealth techniques
        print("Step 2: Trying advanced direct URL bypass...")
        
        events_urls = [
            "https://www.entrio.hr/events",
            "https://entrio.hr/events", 
            "https://www.entrio.hr/events?time=upcoming",
            "https://www.entrio.hr/events?sort=date_asc",
            "https://www.entrio.hr/events?category=music",
            "https://www.entrio.hr/events/zagreb"
        ]
        
        for attempt, url in enumerate(events_urls):
            try:
                print(f"Attempt {attempt + 1}: Trying {url}")
                
                # Wait with human-like delay
                await page.wait_for_timeout(random.randint(5000, 10000))
                
                # Simulate coming from Google search
                await page.set_extra_http_headers({
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Accept-Language': 'hr-HR,hr;q=0.9,en-US;q=0.8,en;q=0.7,de;q=0.6',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Cache-Control': 'max-age=0',
                    'Sec-Ch-Ua': '"Google Chrome";v="120", "Chromium";v="120", "Not A Brand";v="99"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"Windows"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none' if attempt == 0 else 'same-origin',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'Referer': 'https://www.google.com/' if attempt == 0 else 'https://www.entrio.hr/'
                })
                
                # Try navigating to URL
                print(f"Navigating to {url}...")
                response = await page.goto(url, wait_until="networkidle", timeout=30000)
                
                # Wait for page to fully load and any dynamic content
                await page.wait_for_timeout(8000)
                
                # Handle any additional overlays that might appear
                await self.handle_cookie_acceptance(page)
                
                # Check the result
                page_title = await page.title()
                page_url = page.url
                page_content = await page.content()
                
                print(f"Result - URL: {page_url}")
                print(f"Result - Title: {page_title}")
                print(f"Result - Content length: {len(page_content)}")
                
                # More sophisticated detection of successful access
                success_indicators = [
                    "/events" in page_url.lower(),
                    "događaji" in page_title.lower() or "events" in page_title.lower(),
                    len(page_content) > 15000,
                    "event-" in page_content or "dogadaj" in page_content
                ]
                
                failed_indicators = [
                    "Cloudflare" in page_title,
                    "Attention Required" in page_title,
                    "Ray ID" in page_content,
                    "checking your browser" in page_content.lower(),
                    len(page_content) < 10000
                ]
                
                if any(success_indicators) and not any(failed_indicators):
                    print(f"🎉 SUCCESS! Bypassed protection for {url}")
                    print(f"   Title: {page_title}")
                    print(f"   URL: {page_url}")
                    
                    # Try to extract events from this page
                    await self.extract_events_from_current_page(page, all_events, max_pages, fetch_details=fetch_details)
                    return
                else:
                    print(f"❌ Still blocked for {url}")
                    if any(failed_indicators):
                        print(f"   Detected blocking indicators")
                    
            except Exception as e:
                print(f"❌ Failed to access {url}: {e}")
                continue
        
        print("⚠️ All advanced bypass methods failed, using homepage events only")

    async def fetch_event_details(self, page, event_url: str) -> Dict:
        """Fetch detailed address information from event page."""
        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for content to load
            
            # Extract detailed location information using real Entrio.hr selectors
            event_details = await page.evaluate(
                """
                () => {
                    const details = {};
                    
                    // Primary selector - discovered through MCP investigation
                    const locationHeader = document.querySelector('.event-header__location');
                    if (locationHeader && locationHeader.textContent.trim()) {
                        const locationText = locationHeader.textContent.trim();
                        details.full_location = locationText;
                        
                        // Parse "Venue Name, City" format from event detail pages
                        const venueCityParts = locationText.split(',');
                        if (venueCityParts.length >= 2) {
                            details.venue = venueCityParts[0].trim();
                            details.city = venueCityParts[1].trim();
                            details.location = locationText; // "Venue Name, City"
                        } else {
                            details.location = locationText;
                            details.venue = locationText;
                        }
                    }
                    
                    // Fallback selectors for other address information
                    const fallbackSelectors = [
                        '[class*="location"]',
                        '[class*="address"]', 
                        '[class*="venue"]',
                        '[class*="adresa"]',
                        '[class*="lokacija"]',
                        '.event-location',
                        '.venue-info',
                        '.location-details'
                    ];
                    
                    // Only use fallback if primary selector didn't find anything
                    if (!details.full_location) {
                        for (const selector of fallbackSelectors) {
                            const elements = document.querySelectorAll(selector);
                            elements.forEach(el => {
                                const text = el.textContent.trim();
                                if (text && text.length > 2) {
                                    if (!details.full_location || text.length > details.full_location.length) {
                                        details.full_location = text;
                                        details.location = text;
                                    }
                                }
                            });
                        }
                    }
                    
                    // Look for structured address patterns in page content
                    const pageText = document.body.textContent;
                    const addressPatterns = [
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+(?:ulica|cesta|trg|put|avenija|bb)\\s*\\d*[a-z]?)/gi,
                        /(\\d{5}\\s+[A-ZČĆĐŠŽ][a-zčćđšž\\s]+)/gi,
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?\\s*,\\s*\\d{5}\\s+[A-ZČĆĐŠŽ][a-zčćđšž\\s]+)/gi
                    ];
                    
                    for (const pattern of addressPatterns) {
                        const matches = pageText.match(pattern);
                        if (matches && matches.length > 0) {
                            details.street_address = matches[0].trim();
                            break;
                        }
                    }
                    
                    return details;
                }
                """
            )
            
            return event_details
        
        except Exception as e:
            print(f"Error fetching event details from {event_url}: {e}")
            return {}

    async def extract_events_from_current_page(self, page, all_events, max_pages, fetch_details: bool = False):
        """Extract events from the current events page and handle pagination."""
        page_count = 0
        
        while page_count < max_pages:
            try:
                # Wait for page content to load
                await page.wait_for_timeout(3000)
                
                # Scroll down to load any dynamic content
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await page.wait_for_timeout(2000)
                
                # Extract events from current page using real Entrio.hr selectors discovered via MCP
                events_data = await page.evaluate("""
                    () => {
                        const events = [];
                        
                        // Real Entrio.hr event card selectors based on website analysis
                        const eventCards = document.querySelectorAll('article.event-card__wrap');
                        console.log(`Found ${eventCards.length} event cards`);
                        
                        eventCards.forEach(card => {
                            const data = {};
                            
                            // Extract event link using real Entrio selector
                            const linkEl = card.querySelector('a.event-card__action, a[href*="/event/"]');
                            if (linkEl) {
                                data.link = linkEl.href;
                            }
                            
                            // Extract title - look in the card content
                            const titleSelectors = [
                                'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                                '[class*="title"]', '[class*="name"]',
                                '.event-title', '.event-name', '.event-card__title'
                            ];
                            
                            for (const selector of titleSelectors) {
                                const titleEl = card.querySelector(selector);
                                if (titleEl && titleEl.textContent.trim()) {
                                    data.title = titleEl.textContent.trim();
                                    break;
                                }
                            }
                            
                            // If no title found, extract from card text content
                            if (!data.title) {
                                const cardText = card.textContent || '';
                                // Look for patterns like event names (usually the first substantial text)
                                const lines = cardText.split('\\n').map(line => line.trim()).filter(line => line.length > 3);
                                if (lines.length > 0) {
                                    // Skip date lines, find the event name
                                    for (const line of lines) {
                                        if (!line.match(/\\d{1,2}\\.\\d{1,2}\\.\\d{4}/) && line.length > 5) {
                                            data.title = line;
                                            break;
                                        }
                                    }
                                }
                            }
                            
                            // Extract venue/location using the discovered "DD.MM.YYYY. Venue Name, City" pattern
                            const cardText = card.textContent || '';
                            const locationPattern = /(\\d{1,2}\\.\\d{1,2}\\.\\d{4})\\.\\s*(.+)/;
                            const locationMatch = cardText.match(locationPattern);
                            
                            if (locationMatch) {
                                data.date = locationMatch[1]; // Extract date (DD.MM.YYYY)
                                const venueCity = locationMatch[2].trim();
                                
                                // Split venue and city by comma for "Venue Name, City" format
                                const venueCityParts = venueCity.split(',');
                                if (venueCityParts.length >= 2) {
                                    data.venue = venueCityParts[0].trim();
                                    data.city = venueCityParts[1].trim();
                                    data.location = venueCity; // "Venue Name, City"
                                } else {
                                    data.location = venueCity;
                                    data.venue = venueCity;
                                }
                                data.full_location = locationMatch[0]; // Full "DD.MM.YYYY. Venue Name, City"
                            } else {
                                // Fallback: try to find date and location separately
                                const dateMatch = cardText.match(/\\d{1,2}\\.\\d{1,2}\\.\\d{4}/);
                                if (dateMatch) {
                                    data.date = dateMatch[0];
                                }
                                
                                // Try generic location selectors as fallback
                                const locationSelectors = [
                                    '.venue', '.location', '.place', '.where',
                                    '[class*="venue"]', '[class*="location"]',
                                    '[class*="place"]', '[class*="address"]'
                                ];
                                
                                for (const selector of locationSelectors) {
                                    const locationEl = card.querySelector(selector);
                                    if (locationEl && locationEl.textContent.trim()) {
                                        data.location = locationEl.textContent.trim();
                                        break;
                                    }
                                }
                            }
                            
                            // Extract image
                            let imgEl = card.querySelector('img');
                            if (!imgEl && linkEl) {
                                imgEl = linkEl.querySelector('img');
                            }
                            if (imgEl && imgEl.src) {
                                data.image_url = imgEl.src;
                            }
                            
                            // Extract price information
                            const priceSelectors = [
                                '.price', '[class*="price"]', '.event-price',
                                '[class*="cost"]', '[class*="ticket"]'
                            ];
                            
                            for (const selector of priceSelectors) {
                                const priceEl = card.querySelector(selector);
                                if (priceEl && priceEl.textContent.trim()) {
                                    data.price = priceEl.textContent.trim();
                                    break;
                                }
                            }
                            
                            // Croatian address pattern detection in full text content
                            const addressPatterns = [
                                /\\b[\\w\\s]+\\s+\\d+[a-z]?\\s*,\\s*\\d{5}\\s+[\\w\\s]+/gi,  // Street Number, Postal City
                                /\\b[A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+(ulica|cesta|trg|put|avenija|bb)\\s*\\d*[a-z]?\\b/gi,  // Croatian street types
                                /\\b\\d{5}\\s+[A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\b/gi,  // Postal code + city
                                /\\b[A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?\\b/gi  // Simple street + number
                            ];
                            
                            for (const pattern of addressPatterns) {
                                const matches = cardText.match(pattern);
                                if (matches && matches.length > 0) {
                                    data.detected_address = matches[0].trim();
                                    break;
                                }
                            }
                            
                            // Only add events with meaningful data
                            if (data.title || data.link) {
                                events.push(data);
                            }
                        });
                        
                        return events;
                    }
                """)
                
                # Filter out events we already have
                new_events = [event for event in events_data 
                             if not any(existing['link'] == event['link'] for existing in all_events)]
                
                if len(new_events) > 0:
                    all_events.extend(new_events)
                    print(f"Page {page_count + 1}: Found {len(new_events)} new events (Total: {len(all_events)})")
                else:
                    print(f"Page {page_count + 1}: No new events found")
                
                # Look for next page
                next_button = await page.query_selector('a[class*="next"], a[aria-label*="next"], .pagination a:last-child, [class*="pagination"] a:last-child')
                
                if next_button and page_count < max_pages - 1:
                    print("Found next page button, clicking...")
                    await next_button.scroll_into_view_if_needed()
                    await page.wait_for_timeout(1000)
                    await next_button.click()
                    await page.wait_for_timeout(3000)
                    page_count += 1
                else:
                    print("No more pages or reached max pages")
                    break
                    
            except Exception as e:
                print(f"Error on page {page_count + 1}: {e}")
                break


class EntrioScraper:
    """Main scraper class that combines both approaches."""

    def __init__(self):
        self.requests_scraper = EntrioRequestsScraper()
        self.playwright_scraper = EntrioPlaywrightScraper()
        self.transformer = EventDataTransformer()

    async def scrape_events(
        self, max_pages: int = 5, use_playwright: bool = None, fetch_details: bool = False
    ) -> List[EventCreate]:
        """Scrape events and return as EventCreate objects."""
        if use_playwright is None:
            use_playwright = USE_PLAYWRIGHT

        print(f"Starting Entrio.hr scraper (Playwright: {use_playwright}, fetch_details: {fetch_details})")

        # Scrape raw data
        if use_playwright:
            raw_events = await self.playwright_scraper.scrape_with_playwright(
                max_pages=max_pages, fetch_details=fetch_details
            )
        else:
            raw_events = await self.requests_scraper.scrape_all_events(
                max_pages=max_pages
            )

        print(f"Scraped {len(raw_events)} raw events")

        # Transform to EventCreate objects
        events = []
        for raw_event in raw_events:
            event = await self.transformer.transform_to_event_create(raw_event)
            if event:
                events.append(event)

        print(f"Transformed {len(events)} valid events")
        return events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        """Insert events using a bulk query and return number of new rows."""
        if not events:
            return 0

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
                # Use direct SQLAlchemy Core insert to avoid any field mapping issues
                from sqlalchemy import text
                
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


# Convenience functions for API endpoints
async def scrape_entrio_events(max_pages: int = 5, fetch_details: bool = False) -> Dict:
    """Scrape Entrio events and save to database."""
    scraper = EntrioScraper()

    try:
        events = await scraper.scrape_events(max_pages=max_pages, fetch_details=fetch_details)
        saved_count = scraper.save_events_to_database(events)

        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved_count,
            "message": f"Successfully scraped {len(events)} events, saved {saved_count} new events (fetch_details: {fetch_details})",
        }

    except Exception as e:
        return {"status": "error", "message": f"Scraping failed: {str(e)}"}
