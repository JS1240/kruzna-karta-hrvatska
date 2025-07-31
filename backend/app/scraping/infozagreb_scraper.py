"""Enhanced InfoZagreb.hr events scraper with browser automation and multiple fallback strategies."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from datetime import date
from typing import Dict, List, Optional, Any, Union
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from app.scraping.base_scraper import BaseScraper
from backend.app.models.schemas import EventCreate

logger = logging.getLogger(__name__)

BASE_URL = "https://www.infozagreb.hr"
EVENTS_URL = f"{BASE_URL}/en/events"

# Zagreb-specific venue mappings for enhanced location detection
ZAGREB_VENUES = {
    "lisinski": "Lisinski Concert Hall, Zagreb",
    "hnk": "Croatian National Theatre, Zagreb", 
    "dom sportova": "Dom Sportova, Zagreb",
    "arena zagreb": "Arena Zagreb",
    "tvornica kulture": "Tvornica Kulture, Zagreb",
    "vintage industrial bar": "Vintage Industrial Bar, Zagreb",
    "klub": "Club, Zagreb",
    "kino": "Cinema, Zagreb",
    "galerija": "Gallery, Zagreb",
    "muzej": "Museum, Zagreb",
    "trg": "Square, Zagreb",
    "park": "Park, Zagreb",
    "hotel": "Hotel, Zagreb",
    "restoran": "Restaurant, Zagreb",
    "centar": "Center, Zagreb",
    "dvorana": "Hall, Zagreb",
    "teatr": "Theatre, Zagreb",
    "akademija": "Academy, Zagreb",
    "facultet": "Faculty, Zagreb",
    "institut": "Institute, Zagreb",
}






class InfoZagrebTransformer:
    """Transform raw InfoZagreb event data to EventCreate with enhanced address extraction."""
    
    CRO_MONTHS = {
        "siječanj": 1, "veljača": 2, "ožujak": 3, "travanj": 4,
        "svibanj": 5, "lipanj": 6, "srpanj": 7, "kolovoz": 8,
        "rujan": 9, "listopad": 10, "studeni": 11, "prosinac": 12,
        # English fallbacks
        "january": 1, "february": 2, "march": 3, "april": 4,
        "may": 5, "june": 6, "july": 7, "august": 8,
        "september": 9, "october": 10, "november": 11, "december": 12,
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
                        month_num = InfoZagrebTransformer.CRO_MONTHS.get(month.lower())
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
        """Extract and format location from InfoZagreb event data with enhanced address support."""
        # Priority order: detected_address > structured_location > venue + city > venue > city > default
        
        # Highest priority: detected_address from detailed scraping
        if data.get("detected_address"):
            return data["detected_address"].strip()
        
        # Second priority: structured location from detail pages
        if data.get("structured_location"):
            structured_location = data["structured_location"].strip()
            return structured_location
        
        # Third priority: location field from listing or detail pages
        if data.get("location"):
            location = data["location"].strip()
            # If we have city info and it's not in location, add it
            if data.get("city") and data["city"] not in location:
                return f"{location}, {data['city']}"
            return location
        
        # Fourth priority: combine venue information
        venue = data.get("venue", "").strip()
        city = data.get("city", "").strip()
        
        if venue and city and city not in venue:
            location = f"{venue}, {city}"
        elif venue:
            location = venue
        elif city:
            location = city
        else:
            location = ""
        
        # Fallback to Zagreb if nothing found
        return location if location else "Zagreb"

    @staticmethod
    def parse_location_from_text(text: str) -> Dict[str, str]:
        """Parse location information from event text using Zagreb-specific patterns."""
        result = {}
        
        if not text:
            return result
        
        # Pattern 1: LOKACIJA field from detail pages
        lokacija_match = re.search(r"LOKACIJA:\s*([^\n\r]+)", text, re.IGNORECASE)
        if lokacija_match:
            result["structured_location"] = lokacija_match.group(1).strip()
        
        # Pattern 2: ORGANIZATOR/KONTAKT field from detail pages  
        organizator_match = re.search(r"ORGANIZATOR:\s*([^\n\r]+)", text, re.IGNORECASE)
        if organizator_match:
            result["organizator"] = organizator_match.group(1).strip()
        
        kontakt_match = re.search(r"KONTAKT:\s*([^\n\r]+)", text, re.IGNORECASE)
        if kontakt_match:
            result["kontakt"] = kontakt_match.group(1).strip()
        
        # Pattern 3: Enhanced Croatian address patterns for Zagreb region
        address_patterns = [
            # Full address with postal code: "Varšavska 18, 10000 Zagreb"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,?\s*10000\s+Zagreb)",
            # Street with number: "Varšavska 18", "Trg bana Jelačića 7"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+(?:trg|ulica|ul\.|cesta)?\s*\d+[a-z]?)",
            # Postal code with city: "10000 Zagreb"
            r"(10000\s+Zagreb(?:[^\n,]*)?)",
            # Zagreb-specific venue and street patterns
            r"((?:Varšavska|Trg bana Jelačića|Ilica|Frankopanska|Gajeva|Petrinjska|Bogovićeva|Maksimirska|Savska|Heinzelova)\s+\d*[a-z]?)",
            # General Croatian address with number (broader pattern)
            r"([A-ZČĆĐŠŽ][a-zčćđšž]{2,}\s+(?:[A-ZČĆĐŠŽ][a-zčćđšž\s]*\s+)?\d+[a-z]?)"
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                result["detected_address"] = matches[0].strip()
                break
        
        # Extract Zagreb city information
        if "Zagreb" in text:
            result["city"] = "Zagreb"
        
        return result

    @staticmethod
    def get_zagreb_venues():
        """Get list of known Zagreb venues for enhanced recognition."""
        return [
            "Arena Zagreb",
            "Croatian National Theatre", 
            "Lisinski Concert Hall",
            "Vatroslav Lisinski Concert Hall",
            "Zagreb City Museum",
            "Museum of Contemporary Art",
            "Archaeological Museum",
            "Mimara Museum",
            "Croatian Museum of Naïve Art",
            "Zagreb Cathedral",
            "St. Mark's Church",
            "Lotrščak Tower",
            "Ban Jelačić Square",
            "Trg bana Jelačića",
            "King Tomislav Square",
            "Zrinjevac Park",
            "Maksimir Park",
            "Zagreb Fair",
            "Student Centre",
            "Croatian Academy of Sciences and Arts",
            "Zagreb Philharmonic",
            "Dom Sportova",
            "Tvornica Kulture",
            "Vintage Industrial Bar",
            "Kino Europa",
            "Kino Tuškanac",
            "Gradska knjižnica Zagreb",
            "Etnografski muzej",
            "Tehnički muzej",
            "Muzej za umjetnost i obrt",
            "Muzej grada Zagreba",
            "Galerija Klovićevi dvori",
            "Muzej suvremene umjetnosti"
        ]
    
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

            from urllib.parse import urljoin
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
                location=location or "Zagreb",
                description=description or f"Event: {name}",
                price=price or "Check website",
                image=image,
                link=link,
            )
        except Exception:
            return None


class InfoZagrebRequestsScraper:
    """Scraper using httpx and BeautifulSoup with enhanced location extraction."""

    def __init__(self):
        import httpx
        self.client = httpx.AsyncClient(
            headers={
                "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0"
            }
        )

    async def fetch(self, url: str) -> httpx.Response:
        try:
            resp = await self.client.get(url, timeout=30)
            resp.raise_for_status()
            return resp
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            raise

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

        # Enhanced location extraction for InfoZagreb events
        loc_el = soup.select_one(".location, .venue, .place")
        if loc_el:
            data["location"] = loc_el.get_text(strip=True)
        
        # Look for structured location data
        kontakt_section = soup.select_one('[class*="kontakt"], [class*="contact"]')
        if kontakt_section:
            kontakt_text = kontakt_section.get_text(strip=True)
            if kontakt_text:
                data["kontakt"] = kontakt_text
        
        # Look for organizator information
        organizator_section = soup.select_one('[class*="organizator"], [class*="organizer"]')
        if organizator_section:
            organizator_text = organizator_section.get_text(strip=True)
            if organizator_text:
                data["organizator"] = organizator_text
        
        # Store full page text for advanced pattern matching
        data["full_text"] = soup.get_text(separator=" ", strip=True)

        price_el = soup.select_one(".price")
        if price_el:
            data["price"] = price_el.get_text(strip=True)

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

        # Enhanced location extraction for listing elements
        loc_el = el.select_one(".location, .venue, .place")
        if loc_el:
            data["location"] = loc_el.get_text(strip=True)
        
        # Capture full element text for pattern matching
        element_text = el.get_text(separator=" ", strip=True)
        if element_text:
            data["full_text"] = element_text

        price_el = el.select_one(".price")
        if price_el:
            data["price"] = price_el.get_text(strip=True)

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


class InfoZagrebScraper(BaseScraper):
    """Enhanced InfoZagreb.hr scraper with browser automation and multiple fallback strategies."""

    def __init__(self):
        super().__init__(
            base_url=BASE_URL,
            events_url=EVENTS_URL,
            source_name="infozagreb"
        )
        # Initialize scrapers
        self.requests_scraper = InfoZagrebRequestsScraper()
        self.playwright_scraper = InfoZagrebPlaywrightScraper()
        self.transformer = InfoZagrebTransformer()
        
        # Legacy browser automation setup (for compatibility)
        self.playwright = None
        self.browser = None
        self.context = None
        
    async def setup_browser_client(self) -> None:
        """Setup Playwright browser for JavaScript-heavy sites."""
        try:
            from playwright.async_api import async_playwright
            
            if not self.playwright:
                self.playwright = await async_playwright().start()
                self.browser = await self.playwright.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-dev-shm-usage']
                )
                self.context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                logger.info("Playwright browser initialized successfully")
        except ImportError:
            logger.warning("Playwright not available, falling back to static scraping")
        except Exception as e:
            logger.error(f"Failed to setup browser client: {e}")

    async def close_browser(self) -> None:
        """Clean up browser resources."""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            logger.error(f"Error closing browser: {e}")
        finally:
            self.playwright = None
            self.browser = None
            self.context = None


class InfoZagrebPlaywrightScraper:
    """Playwright scraper for enhanced InfoZagreb.hr detail page extraction."""

    async def fetch_event_details(self, page, event_url: str) -> Dict:
        """Fetch detailed address information from individual event page."""
        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for content to load
            
            # Extract detailed location information from event detail page
            event_details = await page.evaluate("""
                () => {
                    const details = {};
                    
                    // Extract LOKACIJA field
                    const pageText = document.body.textContent;
                    const locationMatch = pageText.match(/LOKACIJA:\\s*([^\\n\\r]+)/i);
                    if (locationMatch) {
                        details.structured_location = locationMatch[1].trim();
                    }
                    
                    // Extract ORGANIZATOR field
                    const organizatorMatch = pageText.match(/ORGANIZATOR:\\s*([^\\n\\r]+)/i);
                    if (organizatorMatch) {
                        details.organizator = organizatorMatch[1].trim();
                    }
                    
                    // Extract KONTAKT field
                    const kontaktMatch = pageText.match(/KONTAKT:\\s*([^\\n\\r]+)/i);
                    if (kontaktMatch) {
                        details.kontakt = kontaktMatch[1].trim();
                    }
                    
                    // Look for detailed address patterns in page content
                    const addressPatterns = [
                        // Full address: "Varšavska 18, 10000 Zagreb"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?\\s*,?\\s*10000\\s+Zagreb)/gi,
                        // Street with number: "Varšavska 18", "Trg bana Jelačića 7"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+(?:trg|ulica|ul\\.|cesta)?\\s*\\d+[a-z]?)/gi,
                        // Postal code + city: "10000 Zagreb"
                        /(10000\\s+Zagreb(?:[^\\n,]*)?)/gi,
                        // Zagreb-specific venues
                        /(Arena Zagreb|Croatian National Theatre|Lisinski|Dom Sportova|Tvornica Kulture)/gi
                    ];
                    
                    for (const pattern of addressPatterns) {
                        const matches = pageText.match(pattern);
                        if (matches && matches.length > 0) {
                            // Get the first clean match
                            details.detected_address = matches[0].trim().replace(/\\s+/g, ' ');
                            break;
                        }
                    }
                    
                    // Extract Zagreb city information
                    if (pageText.includes('Zagreb')) {
                        details.city = 'Zagreb';
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

    async def scrape_with_playwright(self, start_url: str = "https://www.infozagreb.hr/en/events", max_pages: int = 5, fetch_details: bool = False) -> List[Dict]:
        """Scrape events using Playwright with enhanced address extraction."""
        try:
            from playwright.async_api import async_playwright
            
            all_events = []
            
            async with async_playwright() as p:
                # Configure browser
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
                        # Look for common cookie consent patterns
                        cookie_selectors = [
                            'button:has-text("Accept")',
                            'button:has-text("I agree")',
                            'button:has-text("Prihvaćam")',
                            '[class*="cookie"] button',
                            '[id*="cookie"] button'
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
                    current_url = start_url
                    
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
                                
                                // Look for event links and information specific to InfoZagreb
                                const eventSelectors = [
                                    'a[href*="/events/"]',
                                    'a[href*="/event/"]',
                                    'a[href*="/dogadaj"]',
                                    'a[href*="/manifestacija"]',
                                    '.event-item a',
                                    '.calendar-item a',
                                    'article a',
                                    '.post a'
                                ];
                                
                                let eventLinks = [];
                                eventSelectors.forEach(selector => {
                                    const links = Array.from(document.querySelectorAll(selector));
                                    eventLinks = eventLinks.concat(links);
                                });
                                
                                // Remove duplicates
                                eventLinks = eventLinks.filter((link, index, self) => 
                                    self.findIndex(l => l.href === link.href) === index
                                );
                                
                                eventLinks.forEach((link, index) => {
                                    if (index >= 20) return; // Limit to prevent too many results
                                    
                                    const data = {};
                                    
                                    // Extract link
                                    if (link.href && link.href.includes('infozagreb.hr')) {
                                        data.link = link.href;
                                    }
                                    
                                    // Extract title from link text
                                    const titleText = link.textContent.trim();
                                    if (titleText && titleText.length > 5) {
                                        data.title = titleText;
                                    }
                                    
                                    // Extract image from nearby img elements
                                    const imgEl = link.querySelector('img') || link.parentElement.querySelector('img');
                                    if (imgEl && imgEl.src) {
                                        data.image_url = imgEl.src;
                                    }
                                    
                                    // Look for date information in parent containers
                                    const parentContainer = link.closest('article, .event-item, .calendar-item, .post, div');
                                    if (parentContainer) {
                                        const containerText = parentContainer.textContent;
                                        
                                        // Look for date patterns
                                        const datePatterns = [
                                            /\\d{1,2}\\.\\d{1,2}\\.\\d{4}/g,
                                            /\\d{4}-\\d{2}-\\d{2}/g,
                                            /\\d{1,2}\\s+\\w+\\s+\\d{4}/g
                                        ];
                                        
                                        datePatterns.forEach(pattern => {
                                            const matches = containerText.match(pattern);
                                            if (matches && !data.date) {
                                                data.date = matches[0];
                                            }
                                        });
                                        
                                        // Look for time patterns
                                        const timeMatch = containerText.match(/\\d{1,2}:\\d{2}/);
                                        if (timeMatch) {
                                            data.time = timeMatch[0];
                                        }
                                        
                                        // Look for Zagreb venues
                                        const venues = ['Arena', 'Lisinski', 'Dom Sportova', 'Tvornica', 'HNK', 'Muzej', 'Galerija'];
                                        venues.forEach(venue => {
                                            if (containerText.includes(venue) && !data.venue) {
                                                const venueMatch = containerText.match(new RegExp(venue + '[^,\\\\n]{0,50}', 'i'));
                                                if (venueMatch) {
                                                    data.venue = venueMatch[0].trim();
                                                }
                                            }
                                        });
                                        
                                        // Store container text for pattern matching
                                        data.full_text = containerText;
                                    }
                                    
                                    // Only add if we have meaningful data
                                    if (data.title && data.link) {
                                        events.push(data);
                                    }
                                });
                                
                                return events;
                            }
                        """)
                        
                        valid_events = [
                            event for event in events_data
                            if event.get("title") and event.get("link")
                        ]
                        
                        # Fetch detailed address information if requested
                        if fetch_details and valid_events:
                            logger.info(f"Fetching detailed address info for {len(valid_events)} events...")
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
                                                logger.info(f"Enhanced event {i+1}/{len(valid_events)}: {event.get('title', 'Unknown')}")
                                            
                                            # Add delay between detail fetches
                                            await page.wait_for_timeout(1000)
                                        
                                        enhanced_events.append(event)
                                        
                                    except Exception as e:
                                        logger.warning(f"Error fetching details for event {event.get('title', 'Unknown')}: {e}")
                                        enhanced_events.append(event)  # Add original event even if detail fetch fails
                                else:
                                    enhanced_events.append(event)
                            
                            valid_events = enhanced_events
                        
                        all_events.extend(valid_events)
                        logger.info(f"Page {page_count}: Found {len(valid_events)} events (Total: {len(all_events)})")
                        
                        # Try to find next page link
                        next_url = None
                        try:
                            next_link = await page.query_selector('a[rel="next"], a.next, .pagination-next a')
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

    def _find_event_containers(self, soup: BeautifulSoup) -> List[Tag]:
        """Enhanced event container detection for InfoZagreb with specific selectors."""
        # InfoZagreb-specific selectors (updated based on site analysis)
        infozagreb_selectors = [
            # Primary InfoZagreb patterns
            "article.event-card",
            ".events-container .event-item",
            "[data-event-id]",
            ".agenda-item",
            ".event-listing .item",
            ".calendar-item",
            ".event-entry",
            
            # Content management system patterns
            ".post-item",
            ".entry-content",
            "article[class*='post']",
            
            # Generic event patterns
            "li.event-item",
            "div.event-item", 
            "article",
            ".events-list li",
            ".event-card",
            ".event",
            
            # Media object patterns (common in Bootstrap-based sites)
            ".media-object",
            ".media",
            
            # Card patterns
            ".card[class*='event']",
            ".card-body",
        ]
        
        for selector in infozagreb_selectors:
            containers = soup.select(selector)
            if containers:
                logger.debug(f"Found {len(containers)} containers with InfoZagreb selector: {selector}")
                return containers
        
        # Advanced fallback: look for structured data
        script_tags = soup.find_all('script', type='application/ld+json')
        if script_tags:
            logger.debug("Found structured data scripts, attempting to parse events")
            structured_events = self._parse_structured_data(script_tags)
            if structured_events:
                return structured_events
        
        # Final fallback to any article or div with event-related classes
        containers = soup.select("article, div[class*='event'], li[class*='event'], div[class*='post']")
        logger.debug(f"Final fallback found {len(containers)} containers")
        return containers
    
    def _parse_structured_data(self, script_tags: List[Tag]) -> List[Tag]:
        """Parse JSON-LD structured data for events."""
        structured_containers = []
        for script in script_tags:
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0] if data else {}
                
                if data.get('@type') == 'Event' or 'Event' in str(data.get('@type', '')):
                    # Create a pseudo-container for structured data
                    container = Tag(name='div', attrs={'class': 'structured-event'})
                    container.string = json.dumps(data)
                    structured_containers.append(container)
                    
            except (json.JSONDecodeError, TypeError) as e:
                logger.debug(f"Failed to parse structured data: {e}")
                continue
                
        return structured_containers

    def parse_listing_element(self, el: Tag) -> Dict[str, Any]:
        """Enhanced parsing of event info from listing page element."""
        data: Dict[str, Any] = {}
        
        # Handle structured data elements
        if el.get('class') and 'structured-event' in el.get('class', []):
            return self._parse_structured_event(el)
        
        # Get full text for advanced parsing
        full_text = el.get_text(separator=" ", strip=True)
        
        # Enhanced title extraction with multiple strategies
        title = self._extract_title(el, full_text)
        if title:
            data["title"] = title
        
        # Enhanced link extraction
        link = self._extract_link(el)
        if link:
            data["link"] = link
            
        # Enhanced date extraction
        date_info = self._extract_date_info(el, full_text)
        if date_info.get("date"):
            data["date"] = date_info["date"]
        if date_info.get("time"):
            data["time"] = date_info["time"]
        
        # Enhanced image extraction
        image = self._extract_image(el)
        if image:
            data["image"] = image
        
        # Enhanced location extraction with Zagreb-specific logic
        location = self._extract_zagreb_location(el, full_text, title or "")
        if location:
            data["location"] = location
            
        # Extract price information
        price = self._extract_price(el, full_text)
        if price:
            data["price"] = price
            
        # Extract description/summary
        description = self._extract_description(el, full_text)
        if description:
            data["description"] = description
        
        # Store full text for enhanced processing
        if full_text:
            data["full_text"] = full_text
        
        return data
    
    def _parse_structured_event(self, el: Tag) -> Dict[str, Any]:
        """Parse structured data event."""
        try:
            event_data = json.loads(el.string)
            return {
                "title": event_data.get("name", ""),
                "description": event_data.get("description", ""),
                "date": event_data.get("startDate", ""),
                "location": self._format_structured_location(event_data.get("location", {})),
                "link": event_data.get("url", ""),
                "image": event_data.get("image", ""),
                "price": self._format_structured_price(event_data.get("offers", {})),
            }
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def _extract_title(self, el: Tag, full_text: str) -> Optional[str]:
        """Extract event title using multiple strategies."""
        # Strategy 1: Look for specific title selectors
        title_selectors = [
            "h1", "h2", "h3", ".title", ".event-title", ".post-title",
            ".entry-title", ".card-title", "a[title]"
        ]
        
        for selector in title_selectors:
            title_el = el.select_one(selector)
            if title_el:
                title = self.clean_text(title_el.get_text(strip=True))
                if title and len(title) > 3:
                    return title
        
        # Strategy 2: Extract from links
        links = el.select("a")
        for link in links:
            link_text = self.clean_text(link.get_text(strip=True))
            if link_text and len(link_text) > 5 and not link_text.lower().startswith(('more', 'read', 'details')):
                return link_text
        
        # Strategy 3: Look for capitalized phrases in text
        lines = [line.strip() for line in full_text.split('\n') if line.strip()]
        for line in lines[:3]:  # Check first 3 lines
            if len(line) > 10 and len(line) < 100:
                return line
                
        return None
    
    def _extract_link(self, el: Tag) -> Optional[str]:
        """Extract event detail link."""
        # Priority: specific event links over generic ones
        links = el.select("a[href]")
        
        for link in links:
            href = link.get("href")
            link_text = link.get_text(strip=True).lower()
            
            # Skip generic navigation links
            if any(skip in link_text for skip in ['home', 'contact', 'about', 'search']):
                continue
                
            if href:
                return self.make_absolute_url(href)
        
        return None
    
    def _extract_date_info(self, el: Tag, full_text: str) -> Dict[str, str]:
        """Extract date and time information."""
        date_info = {}
        
        # Look for semantic date elements
        date_selectors = [
            "time[datetime]", ".date", ".event-date", ".start-date",
            "[data-date]", ".calendar-date"
        ]
        
        for selector in date_selectors:
            date_el = el.select_one(selector)
            if date_el:
                # Try datetime attribute first
                datetime_attr = date_el.get("datetime")
                if datetime_attr:
                    date_info["date"] = datetime_attr
                    break
                
                # Fall back to text content
                date_text = date_el.get_text(strip=True)
                if date_text:
                    date_info["date"] = date_text
                    break
        
        # If no semantic date found, use regex on full text
        if not date_info.get("date"):
            date_patterns = [
                r'\d{1,2}\.\d{1,2}\.\d{4}',  # DD.MM.YYYY
                r'\d{4}-\d{2}-\d{2}',        # YYYY-MM-DD
                r'\d{1,2}\s+\w+\s+\d{4}',    # DD Month YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, full_text)
                if match:
                    date_info["date"] = match.group()
                    break
        
        # Extract time
        time_match = re.search(r'(\d{1,2}:\d{2})', full_text)
        if time_match:
            date_info["time"] = time_match.group(1)
        
        return date_info
    
    def _extract_image(self, el: Tag) -> Optional[str]:
        """Extract event image with multiple strategies."""
        # Strategy 1: Direct img tags
        img_el = el.select_one("img[src]")
        if img_el:
            src = img_el.get("src")
            if src and not src.endswith(('.svg', '.gif')):  # Skip icons
                return self.make_absolute_url(src)
        
        # Strategy 2: Background images in style attributes
        for elem in el.find_all(attrs={"style": True}):
            style = elem.get("style", "")
            bg_match = re.search(r'background-image:\s*url\(["\']?([^"\']+)["\']?\)', style)
            if bg_match:
                return self.make_absolute_url(bg_match.group(1))
        
        return None
    
    def _extract_zagreb_location(self, el: Tag, full_text: str, title: str) -> str:
        """Extract location with Zagreb-specific venue detection."""
        # Look for semantic location elements
        location_selectors = [
            ".location", ".venue", ".place", ".event-location",
            ".address", "[data-location]"
        ]
        
        for selector in location_selectors:
            loc_el = el.select_one(selector)
            if loc_el:
                location = self.clean_text(loc_el.get_text(strip=True))
                if location:
                    return self._enhance_zagreb_location(location, title, full_text)
        
        # Extract from content using Zagreb venue mapping
        return self._enhance_zagreb_location("", title, full_text)
    
    def _enhance_zagreb_location(self, base_location: str, title: str, full_text: str) -> str:
        """Legacy method - use InfoZagrebTransformer.extract_location instead."""
        # Create data dict for new extraction method
        data = {
            "location": base_location,
            "title": title,
            "full_text": full_text
        }
        
        # Parse location information using enhanced patterns
        location_info = InfoZagrebTransformer.parse_location_from_text(full_text)
        data.update(location_info)
        
        # Use enhanced location extraction
        return InfoZagrebTransformer.extract_location(data)
    
    def _extract_price(self, el: Tag, full_text: str) -> Optional[str]:
        """Extract price information."""
        price_selectors = [".price", ".cost", ".event-price", "[data-price]"]
        
        for selector in price_selectors:
            price_el = el.select_one(selector)
            if price_el:
                price = self.clean_text(price_el.get_text(strip=True))
                if price:
                    return price
        
        # Look for price patterns in text
        price_patterns = [
            r'(\d+(?:,\d+)?\s*(?:kn|€|eur|kuna))',
            r'(free|besplatno|gratis)',
            r'(\d+\s*(?:kn|€))',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, full_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _extract_description(self, el: Tag, full_text: str) -> Optional[str]:
        """Extract event description."""
        desc_selectors = [
            ".description", ".summary", ".excerpt", ".event-description",
            ".content", ".text", "p"
        ]
        
        for selector in desc_selectors:
            desc_el = el.select_one(selector)
            if desc_el:
                desc = self.clean_text(desc_el.get_text(separator=" ", strip=True))
                if desc and len(desc) > 20:
                    return desc[:500]  # Limit description length
        
        # Use full text as fallback, truncated
        if len(full_text) > 50:
            return full_text[:300] + "..." if len(full_text) > 300 else full_text
        
        return None
    
    def _format_structured_location(self, location_data: Union[Dict, str]) -> str:
        """Format structured data location."""
        if isinstance(location_data, str):
            return location_data
        
        if isinstance(location_data, dict):
            name = location_data.get("name", "")
            address = location_data.get("address", {})
            
            if isinstance(address, dict):
                street = address.get("streetAddress", "")
                city = address.get("addressLocality", "")
                return f"{name}, {street}, {city}".strip(", ")
            
            return name
        
        return "Zagreb"
    
    def _format_structured_price(self, offers_data: Union[Dict, List]) -> str:
        """Format structured data price."""
        if isinstance(offers_data, list) and offers_data:
            offers_data = offers_data[0]
        
        if isinstance(offers_data, dict):
            price = offers_data.get("price", "")
            currency = offers_data.get("priceCurrency", "")
            return f"{price} {currency}".strip()
        
        return "Check website"

    async def parse_event_detail(self, url: str) -> Dict[str, Any]:
        """Enhanced event detail parsing with fallback strategies."""
        # Try browser automation first for JavaScript-heavy sites
        if self.browser:
            try:
                return await self._parse_event_detail_with_browser(url)
            except Exception as e:
                logger.warning(f"Browser parsing failed for {url}: {e}")
        
        # Fallback to static parsing
        return await self._parse_event_detail_static(url)
    
    async def _parse_event_detail_with_browser(self, url: str) -> Dict[str, Any]:
        """Parse event detail using browser automation."""
        if not self.context:
            await self.setup_browser_client()
        
        if not self.context:
            raise RuntimeError("Browser context not available")
            
        page = await self.context.new_page()
        try:
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for potential JavaScript content loading
            await page.wait_for_timeout(2000)
            
            # Extract structured data first
            structured_data = await page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                    const events = [];
                    scripts.forEach(script => {
                        try {
                            const data = JSON.parse(script.textContent);
                            if (data['@type'] === 'Event' || (Array.isArray(data) && data.some(item => item['@type'] === 'Event'))) {
                                events.push(data);
                            }
                        } catch (e) {}
                    });
                    return events;
                }
            """)
            
            if structured_data:
                for data in structured_data:
                    if isinstance(data, list):
                        data = data[0] if data else {}
                    if data.get('@type') == 'Event':
                        return self._parse_structured_event_data(data)
            
            # Get page content and parse
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            return self._extract_detail_data(soup, url)
            
        finally:
            await page.close()
    
    async def _parse_event_detail_static(self, url: str) -> Dict[str, Any]:
        """Static event detail parsing fallback."""
        try:
            response = await self.fetch_with_retry(url)
            soup = BeautifulSoup(response.text, "html.parser")
            return self._extract_detail_data(soup, url)
            
        except Exception as e:
            logger.warning(f"Failed to parse event detail from {url}: {e}")
            return {}
    
    def _extract_detail_data(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract detailed event data from soup."""
        data: Dict[str, Any] = {}
        
        # Enhanced title extraction
        title_selectors = [
            "h1", ".event-title", ".title", ".post-title", 
            ".entry-title", "[data-title]", "title"
        ]
        for selector in title_selectors:
            title_el = soup.select_one(selector)
            if title_el:
                data["title"] = self.clean_text(title_el.get_text(strip=True))
                break
        
        # Enhanced description extraction
        desc_selectors = [
            ".description", ".event-description", ".summary", ".excerpt",
            ".content", ".post-content", ".entry-content", 
            "article .text", ".event-details"
        ]
        for selector in desc_selectors:
            desc_el = soup.select_one(selector)
            if desc_el:
                desc_text = self.clean_text(desc_el.get_text(separator=" ", strip=True))
                if len(desc_text) > 50:  # Only use substantial descriptions
                    data["description"] = desc_text[:1000]  # Limit length
                    break
        
        # Enhanced date and time extraction
        date_info = self._extract_detail_date_time(soup)
        data.update(date_info)
        
        # Enhanced image extraction
        image = self._extract_detail_image(soup)
        if image:
            data["image"] = image
        
        # Enhanced location extraction
        location = self._extract_detail_location(soup, data.get("title", ""), data.get("description", ""))
        if location:
            data["location"] = location
        
        # Enhanced price extraction
        price = self._extract_detail_price(soup)
        if price:
            data["price"] = price
        
        # Store full page text for advanced pattern matching
        data["full_text"] = soup.get_text(separator=" ", strip=True)
        
        return data
    
    def _extract_detail_date_time(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract date and time from detail page."""
        date_info = {}
        
        # Look for semantic datetime elements
        datetime_selectors = [
            "time[datetime]", "[data-start-date]", "[data-date]",
            ".event-date", ".start-date", ".date"
        ]
        
        for selector in datetime_selectors:
            el = soup.select_one(selector)
            if el:
                # Try datetime attribute
                dt = el.get("datetime") or el.get("data-start-date") or el.get("data-date")
                if dt:
                    date_info["date"] = dt
                    break
                
                # Try text content
                text = el.get_text(strip=True)
                if text and re.search(r'\d{4}', text):
                    date_info["date"] = text
                    break
        
        # Extract from page text if not found
        if not date_info.get("date"):
            page_text = soup.get_text()
            date_patterns = [
                r'\d{1,2}\.\d{1,2}\.\d{4}',  # DD.MM.YYYY
                r'\d{4}-\d{2}-\d{2}',        # YYYY-MM-DD
                r'\d{1,2}\s+\w+\s+\d{4}',    # DD Month YYYY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, page_text)
                if match:
                    date_info["date"] = match.group()
                    break
        
        # Extract time
        time_match = re.search(r'(\d{1,2}:\d{2})', soup.get_text())
        if time_match:
            date_info["time"] = time_match.group(1)
        
        return date_info
    
    def _extract_detail_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main event image from detail page."""
        image_selectors = [
            ".event-image img", ".featured-image img", ".post-thumbnail img",
            "article img", ".hero-image img", ".main-image img"
        ]
        
        for selector in image_selectors:
            img_el = soup.select_one(selector)
            if img_el and img_el.get("src"):
                src = img_el.get("src")
                if src and not src.endswith(('.svg', '.gif', '.ico')):
                    return self.make_absolute_url(src)
        
        # Fallback to any reasonable sized image
        for img in soup.select("img[src]"):
            src = img.get("src")
            if src and not any(skip in src.lower() for skip in ['logo', 'icon', 'avatar', 'button']):
                return self.make_absolute_url(src)
        
        return None
    
    def _extract_detail_location(self, soup: BeautifulSoup, title: str, description: str) -> str:
        """Extract location from detail page."""
        location_selectors = [
            ".location", ".venue", ".event-location", ".address",
            "[data-location]", ".event-venue"
        ]
        
        for selector in location_selectors:
            loc_el = soup.select_one(selector)
            if loc_el:
                location = self.clean_text(loc_el.get_text(strip=True))
                if location:
                    return self._enhance_zagreb_location(location, title, description)
        
        # Use Zagreb venue detection on content
        page_text = soup.get_text()
        return self._enhance_zagreb_location("", title, f"{description} {page_text}")
    
    def _extract_detail_price(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract price from detail page."""
        price_selectors = [
            ".price", ".cost", ".event-price", ".ticket-price",
            "[data-price]", ".admission"
        ]
        
        for selector in price_selectors:
            price_el = soup.select_one(selector)
            if price_el:
                price = self.clean_text(price_el.get_text(strip=True))
                if price:
                    return price
        
        # Look in page text
        page_text = soup.get_text()
        price_patterns = [
            r'(\d+(?:,\d+)?\s*(?:kn|€|eur|kuna))',
            r'(free|besplatno|gratis)',
            r'(\d+\s*(?:kn|€))',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, page_text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        return None
    
    def _parse_structured_event_data(self, data: Dict) -> Dict[str, Any]:
        """Parse structured event data."""
        return {
            "title": data.get("name", ""),
            "description": data.get("description", ""),
            "date": data.get("startDate", ""),
            "time": self._extract_time_from_datetime(data.get("startDate", "")),
            "location": self._format_structured_location(data.get("location", {})),
            "image": data.get("image", ""),
            "price": self._format_structured_price(data.get("offers", {})),
        }
    
    def _extract_time_from_datetime(self, datetime_str: str) -> str:
        """Extract time from ISO datetime string."""
        if not datetime_str:
            return "20:00"
        
        time_match = re.search(r'T(\d{2}:\d{2})', datetime_str)
        if time_match:
            return time_match.group(1)
        
        return "20:00"
    
    async def try_api_endpoints(self) -> List[Dict[str, Any]]:
        """Attempt to discover and use InfoZagreb's event API endpoints."""
        potential_endpoints = [
            f"{self.base_url}/api/events",
            f"{self.base_url}/en/events/data",
            f"{self.base_url}/wp-json/wp/v2/events",
            f"{self.base_url}/api/posts?category=events",
            f"{self.base_url}/wp-json/wp/v2/posts?categories=events",
            f"{self.base_url}/wp-admin/admin-ajax.php?action=get_events",
        ]
        
        events = []
        for endpoint in potential_endpoints:
            try:
                logger.info(f"Trying API endpoint: {endpoint}")
                response = await self.fetch_with_retry(endpoint)
                
                # Check if response is JSON
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    data = response.json()
                    
                    # Try to parse different API response formats
                    api_events = self._parse_api_response(data)
                    if api_events:
                        logger.info(f"Found {len(api_events)} events from API endpoint: {endpoint}")
                        events.extend(api_events)
                        break  # Use first successful endpoint
                        
            except Exception as e:
                logger.debug(f"API endpoint {endpoint} failed: {e}")
                continue
        
        return events
    
    def _parse_api_response(self, data: Union[Dict, List]) -> List[Dict[str, Any]]:
        """Parse various API response formats."""
        events = []
        
        try:
            # Handle different response structures
            if isinstance(data, list):
                # Direct array of events
                for item in data:
                    if isinstance(item, dict):
                        event = self._normalize_api_event(item)
                        if event:
                            events.append(event)
            
            elif isinstance(data, dict):
                # Check for common API wrapper patterns
                event_arrays = [
                    data.get('events', []),
                    data.get('data', []),
                    data.get('results', []),
                    data.get('items', []),
                    data.get('posts', []),
                ]
                
                for array in event_arrays:
                    if isinstance(array, list):
                        for item in array:
                            if isinstance(item, dict):
                                event = self._normalize_api_event(item)
                                if event:
                                    events.append(event)
                        if events:  # Stop at first successful array
                            break
                
                # Handle single event response
                if not events and self._looks_like_event(data):
                    event = self._normalize_api_event(data)
                    if event:
                        events.append(event)
        
        except Exception as e:
            logger.debug(f"Failed to parse API response: {e}")
        
        return events
    
    def _normalize_api_event(self, item: Dict) -> Optional[Dict[str, Any]]:
        """Normalize API event data to standard format."""
        try:
            # Common field mappings
            title = (
                item.get('title') or 
                item.get('name') or 
                item.get('post_title') or
                (item.get('title', {}).get('rendered') if isinstance(item.get('title'), dict) else None)
            )
            
            if not title or len(str(title).strip()) < 3:
                return None
            
            # Extract content/description
            content = (
                item.get('description') or
                item.get('content') or
                item.get('excerpt') or
                item.get('post_content') or
                (item.get('content', {}).get('rendered') if isinstance(item.get('content'), dict) else None) or
                (item.get('excerpt', {}).get('rendered') if isinstance(item.get('excerpt'), dict) else None)
            )
            
            # Extract date
            date_str = (
                item.get('date') or
                item.get('start_date') or
                item.get('event_date') or
                item.get('post_date') or
                item.get('created_at')
            )
            
            # Extract location
            location = (
                item.get('location') or
                item.get('venue') or
                item.get('place') or
                ""
            )
            
            # Extract image
            image = None
            if item.get('featured_media'):
                image = f"{self.base_url}/wp-json/wp/v2/media/{item['featured_media']}"
            else:
                image = (
                    item.get('image') or
                    item.get('thumbnail') or
                    item.get('featured_image')
                )
            
            # Extract link
            link = (
                item.get('link') or
                item.get('url') or
                item.get('permalink') or
                (f"{self.base_url}/events/{item['id']}" if item.get('id') else None)
            )
            
            return {
                "title": str(title).strip(),
                "description": self.clean_text(str(content)) if content else "",
                "date": str(date_str) if date_str else "",
                "location": self._enhance_zagreb_location(str(location) if location else "", str(title), str(content) if content else ""),
                "image": self.make_absolute_url(str(image)) if image else "",
                "link": self.make_absolute_url(str(link)) if link else "",
                "price": item.get('price') or item.get('cost') or "Check website"
            }
            
        except Exception as e:
            logger.debug(f"Failed to normalize API event: {e}")
            return None
    
    def _looks_like_event(self, data: Dict) -> bool:
        """Check if a dictionary looks like an event."""
        event_indicators = [
            'title', 'name', 'event', 'date', 'start_date', 
            'venue', 'location', 'description'
        ]
        
        return any(key in data for key in event_indicators)
    
    async def scrape_with_browser(self, max_pages: int = 10) -> List[EventCreate]:
        """Scrape using browser automation for JavaScript-heavy content."""
        logger.info("Starting browser-based scraping")
        
        try:
            await self.setup_browser_client()
            
            if not self.context:
                raise RuntimeError("Failed to setup browser context")
            
            page = await self.context.new_page()
            
            # Navigate to events page
            await page.goto(self.events_url, wait_until="networkidle", timeout=30000)
            
            # Wait for JavaScript content to load
            await page.wait_for_timeout(3000)
            
            # Try to load more events if pagination exists
            load_more_attempts = 0
            while load_more_attempts < max_pages:
                # Look for load more buttons or pagination
                load_more_selectors = [
                    'button[class*="load-more"]',
                    'a[class*="load-more"]', 
                    '.pagination .next',
                    'button[class*="more"]'
                ]
                
                load_more_found = False
                for selector in load_more_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            await element.click()
                            await page.wait_for_timeout(2000)
                            load_more_found = True
                            break
                    except:
                        continue
                
                if not load_more_found:
                    break
                    
                load_more_attempts += 1
            
            # Get final page content
            content = await page.content()
            soup = BeautifulSoup(content, "html.parser")
            
            # Parse events from the content
            containers = self._find_event_containers(soup)
            events = []
            
            for container in containers:
                if isinstance(container, Tag):
                    event_data = self.parse_listing_element(container)
                    if event_data:
                        event = self.transform_to_event(event_data)
                        if event:
                            events.append(event)
            
            await page.close()
            logger.info(f"Browser scraping found {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"Browser scraping failed: {e}")
            return []
        finally:
            await self.close_browser()
    
    async def scrape_with_api(self, max_pages: int = 10) -> List[EventCreate]:
        """Scrape using API endpoints if available."""
        logger.info("Attempting API-based scraping")
        
        try:
            api_events = await self.try_api_endpoints()
            
            events = []
            for event_data in api_events:
                event = self.transform_to_event(event_data)
                if event:
                    events.append(event)
            
            logger.info(f"API scraping found {len(events)} events")
            return events
            
        except Exception as e:
            logger.error(f"API scraping failed: {e}")
            return []
    
    async def scrape_with_fallbacks(self, max_pages: int = 10) -> List[EventCreate]:
        """Multi-strategy scraping with fallbacks."""
        logger.info("Starting multi-strategy scraping with fallbacks")
        
        strategies = [
            ("API endpoints", self.scrape_with_api),
            ("Browser automation", self.scrape_with_browser),
            ("Static content", self.scrape_all_events),
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                logger.info(f"Trying strategy: {strategy_name}")
                events = await strategy_func(max_pages)
                
                if events and len(events) > 0:
                    logger.info(f"Strategy '{strategy_name}' successful: {len(events)} events found")
                    return events
                else:
                    logger.warning(f"Strategy '{strategy_name}' returned no events")
                    
            except Exception as e:
                logger.warning(f"Strategy '{strategy_name}' failed: {e}")
                continue
        
        logger.warning("All scraping strategies failed")
        return []

    def parse_infozagreb_date(self, date_str: str) -> Optional[date]:
        """InfoZagreb-specific date parsing with enhanced patterns."""
        if not date_str:
            return None
            
        date_str = date_str.strip()
        
        # InfoZagreb specific patterns
        infozagreb_patterns = [
            r'(\d{1,2})\.(\d{1,2})\.(\d{4})',                    # DD.MM.YYYY (Croatian standard)
            r'(\d{4})-(\d{1,2})-(\d{1,2})',                     # YYYY-MM-DD (ISO format)
            r'(\d{1,2})\s+(siječnja|veljače|ožujka|travnja|svibnja|lipnja|srpnja|kolovoza|rujna|listopada|studenoga|prosinca)\s+(\d{4})',  # Croatian months
            r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})',  # English months
            r'(\d{1,2})\.(\d{1,2})\.',                          # DD.MM. (current year)
            r'(\d{1,2})/(\d{1,2})/(\d{4})',                     # MM/DD/YYYY or DD/MM/YYYY
        ]
        
        croatian_months = {
            'siječnja': 1, 'veljače': 2, 'ožujka': 3, 'travnja': 4,
            'svibnja': 5, 'lipnja': 6, 'srpnja': 7, 'kolovoza': 8,
            'rujna': 9, 'listopada': 10, 'studenoga': 11, 'prosinca': 12
        }
        
        english_months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        
        for i, pattern in enumerate(infozagreb_patterns):
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if i == 2:  # Croatian months pattern
                        day, month_name, year = match.groups()
                        month_num = croatian_months.get(month_name.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                    elif i == 3:  # English months pattern
                        day, month_name, year = match.groups()
                        month_num = english_months.get(month_name.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                    elif pattern.endswith(r'(\d{4})'):  # Full date with year
                        if '.' in pattern:  # DD.MM.YYYY
                            day, month, year = match.groups()
                            return date(int(year), int(month), int(day))
                        elif '-' in pattern:  # YYYY-MM-DD
                            year, month, day = match.groups()
                            return date(int(year), int(month), int(day))
                        elif '/' in pattern:  # DD/MM/YYYY (assume European format)
                            day, month, year = match.groups()
                            return date(int(year), int(month), int(day))
                    elif pattern.endswith(r'\.'):  # DD.MM. (assume current year)
                        day, month = match.groups()
                        current_year = date.today().year
                        parsed_date = date(current_year, int(month), int(day))
                        # If date is in the past, assume next year
                        if parsed_date < date.today():
                            parsed_date = date(current_year + 1, int(month), int(day))
                        return parsed_date
                        
                except (ValueError, TypeError) as e:
                    logger.debug(f"Date parsing failed for pattern {pattern} with data {match.groups()}: {e}")
                    continue
        
        # Fallback to base parser
        return self.parse_date(date_str)

    def transform_to_event(self, raw_data: Dict[str, Any]) -> Optional[EventCreate]:
        """Enhanced transformation with InfoZagreb-specific processing."""
        try:
            title = self.clean_text(raw_data.get("title", ""))
            
            # Parse location information from text content
            full_text = raw_data.get("full_text", "") or raw_data.get("description", "")
            location_info = InfoZagrebTransformer.parse_location_from_text(full_text)
            
            # Merge parsed location info with existing data
            enhanced_data = {**raw_data, **location_info}
            
            # Use enhanced location extraction
            location = InfoZagrebTransformer.extract_location(enhanced_data)
            description = self.clean_text(raw_data.get("description", ""))
            price = self.clean_text(raw_data.get("price", ""))
            
            # Enhanced date parsing with InfoZagreb-specific patterns
            date_str = raw_data.get("date", "")
            parsed_date = self.parse_infozagreb_date(date_str)
            if not parsed_date:
                logger.debug(f"Could not parse date '{date_str}' for event '{title}'")
                return None
            
            # Enhanced time parsing
            time_str = raw_data.get("time", "")
            parsed_time = self.parse_time(time_str)
            
            # Enhanced URL handling
            image = raw_data.get("image")
            if image:
                image = self.make_absolute_url(image)
                # Validate image URL
                if not self._is_valid_image_url(image):
                    image = None
            
            link = raw_data.get("link")
            if link:
                link = self.make_absolute_url(link)
            
            # Enhanced validation
            if not title or len(title) < 3:
                logger.debug(f"Event title too short or missing: '{title}'")
                return None
            
            # Ensure location includes Zagreb if it's just a venue name
            if location and "zagreb" not in location.lower():
                location = f"{location}, Zagreb"
            
            # Enhanced description
            if not description and title:
                description = f"Event in Zagreb: {title}"
            
            return EventCreate(
                title=title,
                time=parsed_time,
                date=parsed_date,
                location=location or "Zagreb",
                description=description or f"Event: {title}",
                price=price or "Check website",
                image=image,
                link=link,
                source=self.source_name,
                tags=self._extract_tags(title, description, location)
            )
            
        except Exception as e:
            logger.error(f"Failed to transform event data: {e}")
            return None
    
    def _is_valid_image_url(self, url: str) -> bool:
        """Validate if URL looks like a valid image."""
        if not url:
            return False
        
        # Check for common image extensions
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
        url_lower = url.lower()
        
        # Direct extension check
        if any(url_lower.endswith(ext) for ext in image_extensions):
            return True
        
        # Check for image in URL path
        if any(keyword in url_lower for keyword in ['image', 'img', 'photo', 'picture']):
            return True
        
        # Avoid obviously non-image URLs
        if any(avoid in url_lower for avoid in ['javascript:', 'data:', '#', 'mailto:']):
            return False
        
        return True
    
    def _extract_tags(self, title: str, description: str, location: str) -> List[str]:
        """Extract relevant tags from event content."""
        tags = ["zagreb", "croatia"]
        
        content = f"{title} {description} {location}".lower()
        
        # Event type tags
        event_types = {
            'concert': ['concert', 'koncert', 'glazba', 'music'],
            'theater': ['theater', 'theatre', 'kazalište', 'predstava'],
            'exhibition': ['exhibition', 'izložba', 'galerija', 'gallery'],
            'festival': ['festival', 'festivala'],
            'conference': ['conference', 'konferencija', 'kongres'],
            'workshop': ['workshop', 'radionica', 'seminar'],
            'sports': ['sport', 'utakmica', 'match', 'game'],
            'food': ['food', 'hrana', 'restaurant', 'restoran', 'gastro'],
        }
        
        for tag, keywords in event_types.items():
            if any(keyword in content for keyword in keywords):
                tags.append(tag)
        
        # Venue-based tags
        if any(venue in content for venue in ['lisinski', 'hnk', 'dom sportova']):
            tags.append('venue')
        
        return list(set(tags))  # Remove duplicates

    async def scrape_events(self, max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> List[EventCreate]:
        """Scrape events from InfoZagreb.hr with optional enhanced address extraction."""
        raw_events = []
        
        if use_playwright:
            # Try Playwright first for enhanced extraction
            logger.info("Using Playwright for enhanced scraping...")
            try:
                raw_events = await self.playwright_scraper.scrape_with_playwright(
                    start_url="https://www.infozagreb.hr/en/events", 
                    max_pages=max_pages, 
                    fetch_details=fetch_details
                )
                logger.info(f"Playwright extracted {len(raw_events)} raw events")
            except Exception as e:
                logger.error(f"Playwright failed: {e}, falling back to requests approach")
                raw_events = []
        
        # If Playwright fails or is disabled, use requests approach
        if not raw_events:
            logger.info("Using requests/BeautifulSoup approach...")
            try:
                raw_events = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
                logger.info(f"Requests approach extracted {len(raw_events)} raw events")
            except Exception as e:
                logger.error(f"Requests approach also failed: {e}")
                raw_events = []
            finally:
                await self.requests_scraper.close()
        
        # Transform raw data to EventCreate objects
        events: List[EventCreate] = []
        for item in raw_events:
            event = self.transformer.transform(item)
            if event:
                events.append(event)
        
        logger.info(f"Transformed {len(events)} valid events from {len(raw_events)} raw events")
        return events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        """Save events to database with duplicate prevention."""
        from sqlalchemy import select, tuple_
        from sqlalchemy.dialects.postgresql import insert
        
        from backend.app.core.database import SessionLocal
        from backend.app.models.event import Event
        
        if not events:
            return 0
        
        db = SessionLocal()
        try:
            event_dicts = [e.model_dump() for e in events]
            # Use 'title' instead of 'name' for duplicate checking
            pairs = [(e["title"], e["date"]) for e in event_dicts]
            existing = db.execute(
                select(Event.title, Event.date).where(
                    tuple_(Event.title, Event.date).in_(pairs)
                )
            ).all()
            existing_pairs = set(existing)
            to_insert = [
                e for e in event_dicts if (e["title"], e["date"]) not in existing_pairs
            ]
            if to_insert:
                stmt = insert(Event).values(to_insert)
                stmt = stmt.on_conflict_do_nothing(index_elements=["title", "date"])
                db.execute(stmt)
                db.commit()
                logger.info(f"Saved {len(to_insert)} new InfoZagreb events to database")
                return len(to_insert)
            db.commit()
            return 0
        except Exception as e:
            logger.error(f"Failed to save events to database: {e}")
            db.rollback()
            raise
        finally:
            db.close()


async def scrape_infozagreb_events(max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> Dict:
    """Scrape InfoZagreb.hr events with optional enhanced address extraction."""
    scraper = InfoZagrebScraper()
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
            "message": f"Scraped {len(events)} events from InfoZagreb.hr, saved {saved} new events" + 
                      (" (with enhanced address extraction)" if use_playwright else ""),
        }
    except Exception as e:
        return {"status": "error", "message": f"InfoZagreb scraping failed: {e}"}
