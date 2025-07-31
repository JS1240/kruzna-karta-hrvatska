"""Ulaznice.hr event scraper with BrightData proxy support."""

import asyncio
import logging
import os
import re
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
import requests
from bs4 import BeautifulSoup, Tag
from sqlalchemy.dialects.postgresql import insert

from backend.app.core.database import SessionLocal
from backend.app.models.event import Event
from backend.app.models.schemas import EventCreate

# BrightData configuration (same as other scrapers)
USER = os.getenv("BRIGHTDATA_USER", "demo_user")
PASSWORD = os.getenv("BRIGHTDATA_PASSWORD", "demo_password")
BRIGHTDATA_HOST_RES = "brd.superproxy.io"
BRIGHTDATA_PORT = int(os.getenv("BRIGHTDATA_PORT", 22225))
SCRAPING_BROWSER_EP = f"https://brd.superproxy.io:{BRIGHTDATA_PORT}"
PROXY = f"http://{USER}:{PASSWORD}@{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"

USE_SB = os.getenv("USE_SCRAPING_BROWSER", "0") == "1"
USE_PROXY = os.getenv("USE_PROXY", "0") == "1"

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0",
}

# Configure logging
logger = logging.getLogger(__name__)


class UlazniceDataTransformer:
    """Utilities for cleaning and parsing Ulaznice.hr data."""

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        if not date_str:
            return None
        match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})", date_str)
        if match:
            day, month, year = match.groups()
            try:
                return date(int(year), int(month), int(day))
            except ValueError:
                return None
        year_match = re.search(r"(\d{4})", date_str)
        if year_match:
            try:
                return date(int(year_match.group(1)), 1, 1)
            except ValueError:
                return None
        return None

    @staticmethod
    def clean_text(text: str) -> str:
        if not text:
            return ""
        return " ".join(text.strip().split())

    @staticmethod
    def extract_location(data: Dict) -> str:
        """Extract and format location from Ulaznice.hr event data with enhanced address support."""
        # Priority order: detected_address > lokacija > venue + organizator > venue > city > default
        
        # Highest priority: detected_address from detailed scraping
        if data.get("detected_address"):
            return data["detected_address"].strip()
        
        # Second priority: lokacija field from detail pages (e.g., "Muzej suvremene umjetnosti, MSU, 2. kat")
        if data.get("lokacija"):
            lokacija = data["lokacija"].strip()
            # If we have city info and it's not in lokacija, add it
            if data.get("city") and data["city"] not in lokacija:
                return f"{lokacija}, {data['city']}"
            return lokacija
        
        # Third priority: combine venue and organizator for fuller context
        venue = data.get("venue", "").strip()
        organizator = data.get("organizator", "").strip()
        
        if venue and organizator and organizator != venue:
            # Use organizator as it often contains more complete venue information
            location = organizator
            # Add venue if it provides additional context
            if venue not in organizator and len(venue) > 3:
                location = f"{venue}, {organizator}"
        elif venue:
            location = venue
        elif organizator:
            location = organizator
        else:
            location = ""
        
        # Add city if available and not already included
        if location and data.get("city") and data["city"] not in location:
            location = f"{location}, {data['city']}"
        elif not location and data.get("city"):
            location = data["city"]
        
        # Fourth priority: basic venue field
        if not location:
            location = data.get("venue", "").strip()
        
        # Fallback
        return location if location else "Croatia"

    @staticmethod
    def parse_location_from_text(text: str) -> Dict[str, str]:
        """Parse location information from event text using discovered patterns."""
        result = {}
        
        if not text:
            return result
        
        # Pattern 1: LOKACIJA field from detail pages
        lokacija_match = re.search(r"LOKACIJA:\s*([^\n\r]+)", text, re.IGNORECASE)
        if lokacija_match:
            result["lokacija"] = lokacija_match.group(1).strip()
        
        # Pattern 2: ORGANIZATOR field from detail pages  
        organizator_match = re.search(r"ORGANIZATOR:\s*([^\n\r]+)", text, re.IGNORECASE)
        if organizator_match:
            result["organizator"] = organizator_match.group(1).strip()
        
        # Pattern 3: Croatian address patterns
        address_patterns = [
            # Street name with number: "Ilica 10"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?)",
            # Postal code + city: "10000 Zagreb"
            r"(\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)",
            # Full address: "Ilica 10, 10000 Zagreb"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,\s*\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)"
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text)
            if matches:
                result["detected_address"] = matches[0].strip()
                break
        
        # Extract Croatian city names
        city_patterns = [
            r"\b(Zagreb|Split|Rijeka|Osijek|Zadar|Pula|Slavonski Brod|Karlovac|Varaždin|Šibenik|Sisak|Velika Gorica|Dubrovnik|Bjelovar|Požega|Čakovec|Koprivnica|Gospić|Virovitica|Kutina|Kaštela|Samobor|Vukovar|Poreč|Rovinj|Umag|Krk|Cavtat|Korčula|Hvar|Brač|Vis|Mljet|Ston|Slano|Makarska|Omiš|Trogir|Biograd|Nin|Vodice|Primošten|Murter|Tribunj|Pirovac)\b"
        ]
        
        for pattern in city_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result["city"] = match.group(1).strip()
                break
        
        return result

    @staticmethod
    def transform_to_event_create(scraped: Dict) -> Optional[EventCreate]:
        try:
            name = UlazniceDataTransformer.clean_text(scraped.get("title", ""))
            if not name or len(name) < 3:
                return None
            
            # Parse location information from text content
            full_text = scraped.get("full_text", "") or scraped.get("description", "")
            location_info = UlazniceDataTransformer.parse_location_from_text(full_text)
            
            # Merge parsed location info with existing data
            enhanced_data = {**scraped, **location_info}
            
            # Use enhanced location extraction
            location = UlazniceDataTransformer.extract_location(enhanced_data)
            
            description = UlazniceDataTransformer.clean_text(
                scraped.get("description", "")
            )
            price = UlazniceDataTransformer.clean_text(scraped.get("price", ""))
            date_obj = UlazniceDataTransformer.parse_date(scraped.get("date", ""))
            if not date_obj:
                return None
            time_str = scraped.get("time", "20:00")
            image = scraped.get("image_url")
            if image and not image.startswith("http"):
                image = urljoin("https://www.ulaznice.hr", image)
            link = scraped.get("link")
            if link and not link.startswith("http"):
                link = urljoin("https://www.ulaznice.hr", link)

            return EventCreate(
                title=name,
                date=date_obj,
                time=time_str,
                location=location or "Croatia",
                description=description or f"Event: {name}",
                price=price or "Contact organizer",
                image=image,
                link=link,
            )
        except Exception:
            return None


class UlazniceScraper:
    """Enhanced scraper for https://www.ulaznice.hr/web/events with Playwright support"""

    def __init__(self) -> None:
        self.session = requests.Session()
        self.playwright_scraper = UlaznicePlaywrightScraper()
        self.transformer = UlazniceDataTransformer()

    async def fetch_async(self, url: str) -> httpx.Response:
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
            logger.error(f"Request failed for {url}: {e}")
            raise

    def fetch(self, url: str) -> requests.Response:
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
            logger.error(f"Request failed for {url}: {e}")
            raise

    def parse_event_from_element(self, elem: Tag) -> Dict:
        data: Dict[str, str] = {}
        try:
            # Extract basic event information
            link_el = elem.select_one("a")
            if link_el:
                href = link_el.get("href")
                if href:
                    data["link"] = href
            
            img_el = elem.select_one("img")
            if img_el:
                src = img_el.get("src") or img_el.get("data-src")
                if src:
                    data["image_url"] = src
            
            # Enhanced title extraction
            title_el = elem.select_one(".title, .event-title, h1, h2, h3")
            if title_el:
                data["title"] = title_el.get_text(strip=True)
            elif link_el:
                # Fallback to link text if no specific title element
                link_text = link_el.get_text(strip=True)
                if len(link_text) > 5:
                    data["title"] = link_text
            
            # Enhanced date extraction
            date_el = elem.select_one(".date, time, .event-date")
            if date_el:
                data["date"] = date_el.get_text(strip=True)
            else:
                # Look for date patterns in text content
                full_text = elem.get_text()
                date_match = re.search(r"\d{2}\.\d{2}\.\d{4}", full_text)
                if date_match:
                    data["date"] = date_match.group(0)
            
            # Enhanced venue extraction
            venue_el = elem.select_one(".venue, .location, .lokacija")
            if venue_el:
                data["venue"] = venue_el.get_text(strip=True)
            
            # Enhanced price extraction
            price_el = elem.select_one(".price, .cijena")
            if price_el:
                data["price"] = price_el.get_text(strip=True)
            else:
                # Look for price patterns in text content
                full_text = elem.get_text()
                price_match = re.search(r"\d+\s*€", full_text)
                if price_match:
                    data["price"] = price_match.group(0)
            
            # Enhanced address pattern detection
            full_text = elem.get_text()
            data["full_text"] = full_text  # Store for further processing
            
            # Extract LOKACIJA and ORGANIZATOR if present
            lokacija_match = re.search(r"LOKACIJA:\s*([^\n\r]+)", full_text, re.IGNORECASE)
            if lokacija_match:
                data["lokacija"] = lokacija_match.group(1).strip()
            
            organizator_match = re.search(r"ORGANIZATOR:\s*([^\n\r]+)", full_text, re.IGNORECASE)
            if organizator_match:
                data["organizator"] = organizator_match.group(1).strip()
            
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
                
                # Extract Croatian city names
                city_match = re.search(r"\b(Zagreb|Split|Rijeka|Osijek|Zadar|Pula|Slavonski Brod|Karlovac|Varaždin|Šibenik|Sisak|Velika Gorica|Dubrovnik|Bjelovar|Požega|Čakovec|Koprivnica|Gospić|Virovitica|Kutina|Kaštela|Samobor|Vukovar|Poreč|Rovinj|Umag|Krk|Cavtat|Korčula|Hvar|Brač|Vis|Mljet|Ston|Slano|Makarska|Omiš|Trogir|Biograd|Nin|Vodice|Primošten|Murter|Tribunj|Pirovac)\b", full_text, re.IGNORECASE)
                if city_match:
                    data["city"] = city_match.group(1)
                
                # Look for venue information in the text
                if not data.get("venue") and "Muzej" in full_text:
                    lines = full_text.split("\n")
                    for line in lines:
                        if "Muzej" in line and len(line.strip()) > 3:
                            data["venue"] = line.strip()
                            break
            
        except Exception as e:
            logger.error(f"Error parsing element: {e}")
        return data

    async def scrape_events_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        logger.info(f"Fetching {url}")
        resp = await self.fetch_async(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        events: List[Dict] = []

        # Enhanced selector strategy based on MCP investigation
        selectors = [
            "div.event", 
            "div.card", 
            "article",
            # Additional selectors discovered via MCP investigation
            "div:has(a):has(img)",  # Divs with both links and images
            "[class*='event']",
            "[class*='card']"
        ]
        
        event_elements: List[Tag] = []
        for sel in selectors:
            try:
                event_elements = soup.select(sel)
                if event_elements:
                    logger.info(f"Found {len(event_elements)} elements using selector: {sel}")
                    break
            except Exception:
                continue
        
        # If no specific selectors work, look for elements containing event-like content
        if not event_elements:
            all_divs = soup.find_all('div')
            event_elements = [
                div for div in all_divs 
                if div.get_text() and (
                    'STALNI POSTAV' in div.get_text() or 
                    'Muzej' in div.get_text() or
                    'LOKACIJA' in div.get_text()
                )
            ]
            logger.info(f"Found {len(event_elements)} elements using content-based detection")
        
        for elem in event_elements:
            if isinstance(elem, Tag):
                event_data = self.parse_event_from_element(elem)
                if event_data and (event_data.get("title") or event_data.get("link")):
                    events.append(event_data)

        logger.info(f"Parsed {len(events)} valid events from page")

        # Enhanced next page detection
        next_page_url = None
        next_selectors = [
            'a[rel="next"]', 
            'a.next', 
            'a:contains("Sljedeća")',  # Croatian "Next"
            'a:contains("Dalje")',     # Croatian "Forward"
            '.pagination a:last-child'
        ]
        
        for selector in next_selectors:
            try:
                next_link = soup.select_one(selector)
                if next_link and isinstance(next_link, Tag):
                    href = next_link.get("href")
                    if href and not href.startswith('#'):
                        next_page_url = urljoin(url, href)
                        break
            except Exception:
                continue

        return events, next_page_url

    async def scrape_events(
        self, start_url: str = "https://www.ulaznice.hr/web/events", max_pages: int = 5, 
        use_playwright: bool = True, fetch_details: bool = False
    ) -> List[EventCreate]:
        """Scrape events from Ulaznice.hr with optional detailed address fetching."""
        all_events: List[EventCreate] = []
        raw_events = []
        
        if use_playwright:
            # Try Playwright first for enhanced extraction
            logger.info("Using Playwright for enhanced scraping...")
            try:
                raw_events = await self.playwright_scraper.scrape_with_playwright(
                    start_url=start_url, 
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
            current_url = start_url
            pages = 0

            while current_url and pages < max_pages:
                try:
                    events_data, next_url = await self.scrape_events_page(current_url)
                    raw_events.extend(events_data)
                    pages += 1
                    current_url = next_url
                    await asyncio.sleep(1)
                except Exception as e:
                    logger.error(f"Failed to scrape {current_url}: {e}")
                    break
            
            logger.info(f"Requests approach extracted {len(raw_events)} raw events")
        
        # Transform raw data to EventCreate objects
        for raw_event in raw_events:
            event = self.transformer.transform_to_event_create(raw_event)
            if event:
                all_events.append(event)
        
        logger.info(f"Transformed {len(all_events)} valid events from {len(raw_events)} raw events")
        return all_events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        if not events:
            return 0
        db = SessionLocal()
        try:
            event_dicts = [e.model_dump() for e in events]
            existing_pairs = set(
                db.execute(
                    insert(Event)
                    .returning(Event.title, Event.date)
                    .on_conflict_do_nothing()
                ).fetchall()
            )
            to_insert = [
                e for e in event_dicts if (e["title"], e["date"]) not in existing_pairs
            ]
            if to_insert:
                stmt = insert(Event).values(to_insert)
                stmt = stmt.on_conflict_do_nothing(index_elements=["title", "date"])
                db.execute(stmt)
                db.commit()
                return len(to_insert)
            db.commit()
            return 0
        except Exception as e:
            logger.error(f"Error saving events: {e}")
            db.rollback()
            raise
        finally:
            db.close()


class UlaznicePlaywrightScraper:
    """Playwright scraper for enhanced Ulaznice.hr detail page extraction."""

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
                        details.lokacija = locationMatch[1].trim();
                    }
                    
                    // Extract ORGANIZATOR field
                    const organizatorMatch = pageText.match(/ORGANIZATOR:\\s*([^\\n\\r]+)/i);
                    if (organizatorMatch) {
                        details.organizator = organizatorMatch[1].trim();
                    }
                    
                    // Look for detailed address patterns in page content
                    const addressPatterns = [
                        // Full address: "Ilica 10, 10000 Zagreb"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?\\s*,\\s*\\d{5}\\s+[A-ZČĆĐŠŽ][a-zčćđšž\\s]+)/gi,
                        // Street with number: "Ilica 10"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?)/gi,
                        // Postal code + city: "10000 Zagreb"
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
                    
                    // Extract Croatian city information
                    const cityMatch = pageText.match(/\\b(Zagreb|Split|Rijeka|Osijek|Zadar|Pula|Slavonski Brod|Karlovac|Varaždin|Šibenik|Sisak|Velika Gorica|Dubrovnik|Bjelovar|Požega|Čakovec|Koprivnica|Gospić|Virovitica|Kutina|Kaštela|Samobor|Vukovar|Poreč|Rovinj|Umag|Krk|Cavtat|Korčula|Hvar|Brač|Vis|Mljet|Ston|Slano|Makarska|Omiš|Trogir|Biograd|Nin|Vodice|Primošten|Murter|Tribunj|Pirovac)\\b/i);
                    if (cityMatch) {
                        details.city = cityMatch[1];
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

    async def scrape_with_playwright(self, start_url: str = "https://www.ulaznice.hr/web/events", max_pages: int = 5, fetch_details: bool = False) -> List[Dict]:
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
                    logger.info(f"Navigating to {start_url}")
                    await page.goto(start_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Handle cookie consent if present
                    try:
                        cookie_button = await page.query_selector('button:has-text("Prihvati sve")')
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
                        
                        # Extract events from current page
                        events_data = await page.evaluate("""
                            () => {
                                const events = [];
                                
                                // Look for event elements containing event information
                                const allElements = document.querySelectorAll('*');
                                const eventElements = [];
                                
                                for (const element of allElements) {
                                    const text = element.textContent;
                                    if (text.includes('STALNI POSTAV') || 
                                        (text.includes('LOKACIJA') && text.includes('ORGANIZATOR')) ||
                                        (element.querySelector('a') && text.includes('Muzej'))) {
                                        eventElements.push(element);
                                    }
                                }
                                
                                eventElements.forEach((container, index) => {
                                    if (index >= 20) return; // Limit to prevent too many results
                                    
                                    const data = {};
                                    
                                    // Extract title
                                    const titleSelectors = ['h1', 'h2', 'h3', 'a', 'strong'];
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
                                        data.image_url = imgEl.src;
                                    }
                                    
                                    // Extract venue/location from text
                                    const text = container.textContent;
                                    if (text.includes('Muzej')) {
                                        const lines = text.split('\\n').map(line => line.trim()).filter(line => line);
                                        const venueLine = lines.find(line => line.includes('Muzej'));
                                        if (venueLine) {
                                            data.venue = venueLine;
                                        }
                                    }
                                    
                                    // Extract date
                                    const dateMatch = text.match(/\\d{2}\\.\\d{2}\\.\\d{4}/);
                                    if (dateMatch) {
                                        data.date = dateMatch[0];
                                    }
                                    
                                    // Extract price
                                    const priceMatch = text.match(/\\d+\\s*€/);
                                    if (priceMatch) {
                                        data.price = priceMatch[0];
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
                            next_link = await page.query_selector('a[rel="next"], a.next, a:has-text("Sljedeća")')
                            if next_link:
                                next_href = await next_link.get_attribute('href')
                                if next_href and not next_href.startswith('#'):
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


async def scrape_ulaznice_events(max_pages: int = 5, fetch_details: bool = False) -> Dict:
    """Scrape Ulaznice.hr events and save to database with optional detailed address fetching."""
    scraper = UlazniceScraper()
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
            "message": f"Successfully scraped {len(events)} events from Ulaznice.hr, saved {saved} new events" + 
                      (" (with detailed address info)" if fetch_details else ""),
        }
    except Exception as e:
        return {"status": "error", "message": f"Ulaznice.hr scraping failed: {e}"}
