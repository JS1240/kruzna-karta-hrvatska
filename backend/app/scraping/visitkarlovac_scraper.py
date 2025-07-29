"""VisitKarlovac.hr events scraper with BrightData support."""

from __future__ import annotations

import asyncio
import os
import re
from datetime import date
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
SCRAPING_BROWSER_EP = f"https://brd.superproxy.io:{BRIGHTDATA_PORT}"
PROXY = f"http://{USER}:{PASSWORD}@{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"

USE_SB = os.getenv("USE_SCRAPING_BROWSER", "0") == "1"
USE_PROXY = os.getenv("USE_PROXY", "0") == "1"

BASE_URL = "https://visitkarlovac.hr"
EVENTS_URL = f"{BASE_URL}/en/events"

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0",
}


class VisitKarlovacTransformer:
    """Transform raw event data to :class:`EventCreate`."""

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
                        month_num = VisitKarlovacTransformer.CRO_MONTHS.get(month.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                    elif pattern.startswith("(\\d{4})"):
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
        """Extract and format location from VisitKarlovac event data with enhanced address support."""
        # Priority order: detected_address > venue_address > venue + city > location > city > default
        
        # Highest priority: detected_address from detailed scraping
        if data.get("detected_address"):
            return data["detected_address"].strip()
        
        # Second priority: structured venue address
        if data.get("venue_address"):
            venue_addr = data["venue_address"].strip()
            if data.get("city") and data["city"] not in venue_addr:
                return f"{venue_addr}, {data['city']}"
            return venue_addr
        
        # Third priority: venue name with city
        if data.get("venue") and data.get("city"):
            return f"{data['venue']}, {data['city']}"
        
        # Fourth priority: basic location field
        location = data.get("location", "").strip()
        if location and location != "Karlovac":
            # Add city if available and not already included
            if data.get("city") and data["city"] not in location:
                return f"{location}, {data['city']}"
            return location
        
        # Fifth priority: city only
        if data.get("city"):
            return data["city"].strip()
        
        # Sixth priority: basic venue field
        if data.get("venue"):
            venue = data["venue"].strip()
            # Add Karlovac if venue doesn't include it
            if "Karlovac" not in venue:
                return f"{venue}, Karlovac"
            return venue
        
        # Fallback
        return "Karlovac"
    
    @staticmethod
    def parse_location_from_text(text: str) -> Dict[str, str]:
        """Parse location information from event text using Croatian address patterns."""
        result = {}
        
        if not text:
            return result
        
        # Croatian address patterns for Karlovac region
        address_patterns = [
            # Street name with number: "Trg bana Jelačića 1"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)",
            # Postal code + city: "47000 Karlovac"
            r"(\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)",
            # Full address: "Trg bana Jelačića 1, 47000 Karlovac"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,\s*\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)"
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text)
            if matches:
                result["detected_address"] = matches[0].strip()
                break
        
        # Extract city names (Karlovac region)
        city_patterns = [
            r"\b(Karlovac|Duga Resa|Ozalj|Ogulin|Plaški|Slunj|Vojnić|Cetingrad|Krnjak|Lasinja|Netretić|Ribnik|Barilović|Bosiljevo|Draganić|Generalski Stol|Josipdol|Kamanje|Krašić|Veljun|Žakanje)\b"
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["city"] = match.group(1).strip()
                break
        
        # Look for venue information
        venue_patterns = [
            r"\b(HNK|Kazalište|Muzej|Galerija|Kino|Dom kulture|Kulturni centar|Športska dvorana|Gradska vijećnica|Aquatika|Korana|Dubovac)\b"
        ]
        
        for pattern in venue_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # Look for more context around the match
                start_pos = max(0, match.start() - 20)
                end_pos = min(len(text), match.end() + 20)
                context = text[start_pos:end_pos].strip()
                result["venue"] = context
                break
        
        return result

    @classmethod
    def transform(cls, data: Dict) -> Optional[EventCreate]:
        try:
            name = cls.clean_text(data.get("title", ""))
            
            # Parse location information from text content
            full_text = data.get("full_text", "") or data.get("description", "")
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

            return EventCreate(
                title=name,
                date=parsed_date,
                time=parsed_time,
                location=location,
                description=description or f"Event in Karlovac: {name}",
                price=price or "Check website",
                image=image,
                link=link,
            )
        except Exception:
            return None


class VisitKarlovacRequestsScraper:
    """Scraper using httpx with optional BrightData proxy."""

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

        # Enhanced location extraction with multiple selectors
        location_selectors = [
            ".location", ".venue", ".place", ".lokacija", ".adresa", ".mjesto",
            ".event-location", ".venue-info", ".address", "[class*='location']",
            "[class*='venue']", "[class*='address']", "[class*='place']"
        ]
        
        for selector in location_selectors:
            loc_el = soup.select_one(selector)
            if loc_el:
                location_text = loc_el.get_text(strip=True)
                if location_text:
                    data["location"] = location_text
                    break

        # Get full page text for address pattern detection
        full_text = soup.get_text(separator=" ", strip=True)
        data["full_text"] = full_text
        
        # Apply Croatian address pattern detection
        if full_text:
            # Look for Croatian address patterns
            address_patterns = [
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,\s*\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)",  # Full address
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)",  # Street + number
                r"(\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)"  # Postal code + city
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, full_text)
                if matches:
                    data["detected_address"] = matches[0].strip()
                    break
            
            # Extract city names (Karlovac region)
            city_match = re.search(r"\b(Karlovac|Duga Resa|Ozalj|Ogulin|Plaški|Slunj|Vojnić|Cetingrad|Krnjak|Lasinja|Netretić|Ribnik|Barilović|Bosiljevo|Draganić|Generalski Stol|Josipdol|Kamanje|Krašić|Veljun|Žakanje)\b", full_text, re.IGNORECASE)
            if city_match:
                data["city"] = city_match.group(1)
            
            # Look for venue information
            venue_patterns = [
                r"\b(HNK[^.]*Karlovac)",  # HNK Karlovac
                r"\b(Kazalište[^.]*)",    # Theater names
                r"\b(Muzej[^.]*)",       # Museum names
                r"\b(Galerija[^.]*)",    # Gallery names
                r"\b(Dom kulture[^.]*)", # Cultural centers
                r"\b(Aquatika[^.]*)",    # Aquatika aquarium
                r"\b(Dubovac[^.]*)"      # Dubovac castle
            ]
            
            for pattern in venue_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    venue_name = match.group(1).strip()
                    if len(venue_name) > 3:  # Valid venue name
                        data["venue"] = venue_name
                        break

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

        # Enhanced location extraction with multiple selectors
        location_selectors = [
            ".location", ".venue", ".place", ".lokacija", ".adresa", ".mjesto",
            ".event-location", ".venue-info", ".address", "[class*='location']",
            "[class*='venue']", "[class*='address']", "[class*='place']"
        ]
        
        for selector in location_selectors:
            loc_el = el.select_one(selector)
            if loc_el:
                location_text = loc_el.get_text(strip=True)
                if location_text:
                    data["location"] = location_text
                    break

        # Get full text for address pattern detection
        full_text = el.get_text(separator=" ", strip=True)
        data["full_text"] = full_text
        
        # Apply Croatian address pattern detection
        if full_text:
            # Look for Croatian address patterns
            address_patterns = [
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,\s*\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)",  # Full address
                r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)",  # Street + number
                r"(\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)"  # Postal code + city
            ]
            
            for pattern in address_patterns:
                matches = re.findall(pattern, full_text)
                if matches:
                    data["detected_address"] = matches[0].strip()
                    break
            
            # Extract city names (Karlovac region)
            city_match = re.search(r"\b(Karlovac|Duga Resa|Ozalj|Ogulin|Plaški|Slunj|Vojnić|Cetingrad|Krnjak|Lasinja|Netretić|Ribnik|Barilović|Bosiljevo|Draganić|Generalski Stol|Josipdol|Kamanje|Krašić|Veljun|Žakanje)\b", full_text, re.IGNORECASE)
            if city_match:
                data["city"] = city_match.group(1)
            
            # Look for venue information in listing text
            if not data.get("venue") and ("HNK" in full_text or "Kazalište" in full_text or 
                                        "Muzej" in full_text or "Galerija" in full_text or
                                        "Aquatika" in full_text or "Dubovac" in full_text):
                venue_patterns = [
                    r"\b(HNK[^.]*Karlovac)",
                    r"\b(Kazalište[^.]*)",
                    r"\b(Muzej[^.]*)", 
                    r"\b(Galerija[^.]*)",
                    r"\b(Dom kulture[^.]*)",
                    r"\b(Aquatika[^.]*)",
                    r"\b(Dubovac[^.]*)"
                ]
                
                for pattern in venue_patterns:
                    match = re.search(pattern, full_text, re.IGNORECASE)
                    if match:
                        venue_name = match.group(1).strip()
                        if len(venue_name) > 3:
                            data["venue"] = venue_name
                            break

        return data

    async def scrape_events_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        resp = await self.fetch(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        events: List[Dict] = []
        containers: List[Tag] = []
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


class VisitKarlovacPlaywrightScraper:
    """Playwright scraper for enhanced VisitKarlovac detail page extraction."""

    async def fetch_event_details(self, page, event_url: str) -> Dict:
        """Fetch detailed address information from individual event page."""
        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for content to load
            
            # Extract detailed location information from event detail page
            event_details = await page.evaluate("""
                () => {
                    const details = {};
                    
                    // Look for detailed location information
                    const locationSelectors = [
                        '.location', '.venue', '.place', '.lokacija', '.adresa', '.mjesto',
                        '.event-location', '.venue-info', '.address', '[class*="location"]',
                        '[class*="venue"]', '[class*="address"]', '[class*="place"]'
                    ];
                    
                    for (const selector of locationSelectors) {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const text = el.textContent.trim();
                            if (text && text.length > 2) {
                                if (!details.venue_address || text.length > details.venue_address.length) {
                                    details.venue_address = text;
                                }
                            }
                        });
                    }
                    
                    // Look for detailed address patterns in page content
                    const pageText = document.body.textContent;
                    const addressPatterns = [
                        // Full address: "Trg bana Jelačića 1, 47000 Karlovac"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?\\s*,\\s*\\d{5}\\s+[A-ZČĆĐŠŽ][a-zčćđšž\\s]+)/gi,
                        // Street with number: "Trg bana Jelačića 1"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?)/gi,
                        // Postal code + city: "47000 Karlovac"
                        /(\\d{5}\\s+[A-ZČĆĐŠŽ][a-zčćđšž\\s]+)/gi
                    ];
                    
                    for (const pattern of addressPatterns) {
                        const matches = pageText.match(pattern);
                        if (matches && matches.length > 0) {
                            // Get the first clean match
                            details.detected_address = matches[0].trim().replace(/\\s+/g, ' ');
                            break;
                        }
                    }
                    
                    // Extract Karlovac region city information
                    const cityMatch = pageText.match(/\\b(Karlovac|Duga Resa|Ozalj|Ogulin|Plaški|Slunj|Vojnić|Cetingrad|Krnjak|Lasinja|Netretić|Ribnik|Barilović|Bosiljevo|Draganić|Generalski Stol|Josipdol|Kamanje|Krašić|Veljun|Žakanje)\\b/i);
                    if (cityMatch) {
                        details.city = cityMatch[1];
                    }
                    
                    // Look for venue information in various elements
                    const venueSelectors = [
                        '.venue', '.venue-name', '.location-name',
                        '[class*="venue"]', '[class*="hall"]', '[class*="theater"]',
                        '.event-venue', '.event-location-name'
                    ];
                    
                    for (const selector of venueSelectors) {
                        const venueEl = document.querySelector(selector);
                        if (venueEl && venueEl.textContent.trim()) {
                            details.venue = venueEl.textContent.trim();
                            break;
                        }
                    }
                    
                    // Look for specific Karlovac venues in text
                    const venuePatterns = [
                        /\\b(HNK[^.]*Karlovac)/gi,
                        /\\b(Kazalište[^.]*)/gi,
                        /\\b(Muzej[^.]*)/gi,
                        /\\b(Galerija[^.]*)/gi,
                        /\\b(Dom kulture[^.]*)/gi,
                        /\\b(Aquatika[^.]*)/gi,
                        /\\b(Dubovac[^.]*)/gi
                    ];
                    
                    for (const pattern of venuePatterns) {
                        const matches = pageText.match(pattern);
                        if (matches && matches.length > 0) {
                            const venueName = matches[0].trim();
                            if (venueName.length > 3) {
                                details.venue = venueName;
                                break;
                            }
                        }
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

    async def scrape_with_playwright(self, start_url: str = EVENTS_URL, max_pages: int = 5, fetch_details: bool = False) -> List[Dict]:
        """Scrape events using Playwright with enhanced address extraction."""
        try:
            from playwright.async_api import async_playwright
            
            all_events = []
            
            async with async_playwright() as p:
                # Configure browser
                if USE_PROXY:
                    # Use proxy configuration
                    browser = await p.chromium.launch(
                        headless=True,
                        proxy={
                            "server": PROXY
                        }
                    )
                else:
                    browser = await p.chromium.launch(headless=True)
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                )
                
                page = await context.new_page()
                
                try:
                    page_count = 0
                    current_url = start_url
                    
                    while current_url and page_count < max_pages:
                        page_count += 1
                        print(f"Scraping page {page_count}: {current_url}")
                        
                        await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
                        await page.wait_for_timeout(3000)
                        
                        # Extract events from current page
                        events_data = await page.evaluate("""
                            () => {
                                const events = [];
                                
                                // Look for event containers
                                const eventSelectors = [
                                    'li.event-item', 'div.event-item', 'article', '.events-list li',
                                    '.event', '.card', '[class*="event"]', '[class*="card"]'
                                ];
                                
                                let eventElements = [];
                                for (const selector of eventSelectors) {
                                    const elements = document.querySelectorAll(selector);
                                    if (elements.length > 0) {
                                        eventElements = Array.from(elements);
                                        break;
                                    }
                                }
                                
                                eventElements.forEach((container, index) => {
                                    if (index >= 20) return; // Limit to prevent too many results
                                    
                                    const data = {};
                                    
                                    // Extract title
                                    const titleSelectors = ['h1', 'h2', 'h3', 'a', 'strong', '.title'];
                                    for (const selector of titleSelectors) {
                                        const titleEl = container.querySelector(selector);
                                        if (titleEl && titleEl.textContent.trim().length > 3) {
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
                                    const dateSelectors = ['.date', 'time', '.event-date'];
                                    for (const selector of dateSelectors) {
                                        const dateEl = container.querySelector(selector);
                                        if (dateEl && dateEl.textContent.trim()) {
                                            data.date = dateEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    // Extract location
                                    const locationSelectors = [
                                        '.location', '.venue', '.place', '.lokacija', '.mjesto',
                                        '[class*="location"]', '[class*="venue"]', '[class*="place"]'
                                    ];
                                    for (const selector of locationSelectors) {
                                        const locEl = container.querySelector(selector);
                                        if (locEl && locEl.textContent.trim()) {
                                            data.location = locEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    // Store full text for further processing
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
                            print(f"Fetching detailed address info for {len(valid_events)} events...")
                            enhanced_events = []
                            
                            for i, event in enumerate(valid_events):
                                if event.get("link"):
                                    try:
                                        # Rate limiting - fetch details for every 3rd event to avoid overwhelming server
                                        if i % 3 == 0:
                                            details = await self.fetch_event_details(page, event["link"])
                                            if details:
                                                # Merge detailed information
                                                event.update(details)
                                                print(f"Enhanced event {i+1}/{len(valid_events)}: {event.get('title', 'Unknown')}")
                                            
                                            # Add delay between detail fetches
                                            await page.wait_for_timeout(1000)
                                        
                                        enhanced_events.append(event)
                                        
                                    except Exception as e:
                                        print(f"Error fetching details for event {event.get('title', 'Unknown')}: {e}")
                                        enhanced_events.append(event)  # Add original event even if detail fetch fails
                                else:
                                    enhanced_events.append(event)
                            
                            valid_events = enhanced_events
                        
                        all_events.extend(valid_events)
                        print(f"Page {page_count}: Found {len(valid_events)} events (Total: {len(all_events)})")
                        
                        # Try to find next page link
                        next_url = None
                        try:
                            next_link = await page.query_selector('a[rel="next"], .pagination-next a, a.next')
                            if next_link:
                                next_href = await next_link.get_attribute('href')
                                if next_href and not next_href.startswith('#'):
                                    next_url = urljoin(current_url, next_href)
                        except:
                            pass
                        
                        current_url = next_url
                        
                        if not current_url:
                            print("No more pages found")
                            break
                    
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


class VisitKarlovacScraper:
    """High level scraper for VisitKarlovac.hr."""

    def __init__(self) -> None:
        self.requests_scraper = VisitKarlovacRequestsScraper()
        self.playwright_scraper = VisitKarlovacPlaywrightScraper()
        self.transformer = VisitKarlovacTransformer()

    async def scrape_events(self, max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> List[EventCreate]:
        """Scrape events from VisitKarlovac.hr with optional detailed address fetching."""
        raw_events = []
        
        if use_playwright:
            # Try Playwright first for enhanced extraction
            print("Using Playwright for enhanced scraping...")
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
            raw_events = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
            await self.requests_scraper.close()
            print(f"Requests approach extracted {len(raw_events)} raw events")
        
        # Transform raw data to EventCreate objects
        events: List[EventCreate] = []
        for raw_event in raw_events:
            event = self.transformer.transform(raw_event)
            if event:
                events.append(event)
        
        print(f"Transformed {len(events)} valid events from {len(raw_events)} raw events")
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
                stmt = stmt.on_conflict_do_nothing(index_elements=["title", "date"])
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


async def scrape_visitkarlovac_events(max_pages: int = 5, fetch_details: bool = False) -> Dict:
    """Scrape VisitKarlovac.hr events and save to database with optional detailed address fetching."""
    scraper = VisitKarlovacScraper()
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
            "message": f"Successfully scraped {len(events)} events from VisitKarlovac.hr, saved {saved} new events" + 
                      (f" (with detailed address info)" if fetch_details else ""),
        }
    except Exception as e:
        return {"status": "error", "message": f"VisitKarlovac scraping failed: {e}"}
