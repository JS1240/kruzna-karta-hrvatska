"""VisitVarazdin.hr events scraper with optional Bright Data proxy."""

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

BASE_URL = "https://visitvarazdin.hr"
EVENTS_URL = f"{BASE_URL}/en/events"



class VisitVarazdinDataTransformer:
    """Transform raw VisitVarazdin event data to :class:`EventCreate`."""

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
                        month_num = VisitVarazdinDataTransformer.CRO_MONTHS.get(month.lower())
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
        """Extract and format location from VisitVarazdin event data with enhanced address support."""
        # Priority order: detected_address > structured_location > venue + city > venue > city > default
        
        # Highest priority: detected_address from detailed scraping
        if data.get("detected_address"):
            return data["detected_address"].strip()
        
        # Second priority: structured location from EventON plugin (e.g., "Gradski bazeni Varaždin, Zagrebačka 85a, Varaždin")
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
        
        # Fallback to Varaždin if nothing found
        return location if location else "Varaždin"

    @staticmethod
    def parse_location_from_text(text: str) -> Dict[str, str]:
        """Parse location information from event text using Varaždin-specific patterns."""
        result = {}
        
        if not text:
            return result
        
        # Pattern 1: EventON structured location format
        structured_location_match = re.search(r"LokacijaGradski\s+[^,\n]+,\s*[^,\n]+,\s*Varaždin", text, re.IGNORECASE)
        if structured_location_match:
            result["structured_location"] = structured_location_match.group(0).replace("Lokacija", "").strip()
        
        # Pattern 2: Direct venue + address + city format from EventON
        venue_address_match = re.search(r"([^,\n]+),\s*([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?),\s*(Varaždin)", text)
        if venue_address_match:
            venue, street, city = venue_address_match.groups()
            result["structured_location"] = f"{venue.strip()}, {street.strip()}, {city.strip()}"
        
        # Pattern 3: Enhanced Croatian address patterns for Varaždin region
        address_patterns = [
            # Full address with postal code: "Zagrebačka 85a, 42000 Varaždin"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,?\s*42000\s+Varaždin)",
            # Street with number: "Zagrebačka 85a", "Franjevački trg 10"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+(?:trg|ulica|ul\.|cesta)?\s*\d+[a-z]?)",
            # Postal code with city: "42000 Varaždin"
            r"(42000\s+Varaždin(?:[^\n,]*)?)",
            # Varaždin-specific street patterns with Croatian prefixes
            r"((?:Zagrebačka|Franjevački|Trg|Ulica|Put|Poljana|Pavlinska|Kapucinska)\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]*\d*[a-z]?)",
            # General Croatian address with number (broader pattern)
            r"([A-ZČĆĐŠŽ][a-zčćđšž]{2,}\s+(?:[A-ZČĆĐŠŽ][a-zčćđšž\s]*\s+)?\d+[a-z]?)"
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                result["detected_address"] = matches[0].strip()
                break
        
        # Extract Varaždin city information
        if "Varaždin" in text:
            result["city"] = "Varaždin"
        
        return result

    @staticmethod
    def get_varazdin_venues():
        """Get list of known Varaždin venues for enhanced recognition."""
        return [
            "Gradski bazeni Varaždin",
            "Palača Herzer", 
            "Palača Patačić",
            "GMV",
            "HDLU Varaždin",
            "Kula stražara",
            "HNK Varaždin",
            "Gradska knjižnica Varaždin",
            "Franjevački trg",
            "Trg bana Jelačića",
            "Kulturni centar Varaždin",
            "Spomen-dom",
            "Koncertna dvorana Varaždin",
            "Dvorana Zlatko Crnković",
            "Arena Varaždin"
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
                location=location or "Varaždin",
                description=description or f"Event: {name}",
                price=price or "Check website",
                image=image,
                link=link,
            )
        except Exception:
            return None


class VisitVarazdinRequestsScraper:
    """Scraper using httpx and BeautifulSoup with optional Bright Data proxy."""

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

        # Enhanced location extraction for EventON plugin
        loc_el = soup.select_one(".location, .venue, .place")
        if loc_el:
            data["location"] = loc_el.get_text(strip=True)
        
        # Look for EventON structured location data
        eventon_location = soup.select_one('[class*="location"]')
        if eventon_location:
            location_text = eventon_location.get_text(strip=True)
            if location_text and "," in location_text:
                data["structured_location"] = location_text
        
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


class VisitVarazdinPlaywrightScraper:
    """Playwright scraper for enhanced VisitVarazdin.hr detail page extraction."""

    async def fetch_event_details(self, page, event_url: str) -> Dict:
        """Fetch detailed address information from individual event page."""
        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for content to load
            
            # Extract detailed location information from EventON plugin
            event_details = await page.evaluate("""
                () => {
                    const details = {};
                    
                    // Extract location from EventON structure
                    const locationEl = document.querySelector('.location, [class*="location"]');
                    if (locationEl) {
                        details.structured_location = locationEl.textContent.trim();
                    }
                    
                    // Extract venue information
                    const venueEl = document.querySelector('.venue, [class*="venue"]');
                    if (venueEl) {
                        details.venue = venueEl.textContent.trim();
                    }
                    
                    // Look for detailed address patterns in page content
                    const pageText = document.body.textContent;
                    const addressPatterns = [
                        // Full address: "Zagrebačka 85a, 42000 Varaždin"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?\\s*,?\\s*42000\\s+Varaždin)/gi,
                        // Street with number: "Zagrebačka 85a", "Franjevački trg 10"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+(?:trg|ulica|ul\\.|cesta)?\\s*\\d+[a-z]?)/gi,
                        // Postal code + city: "42000 Varaždin"
                        /(42000\\s+Varaždin(?:[^\\n,]*)?)/gi
                    ];
                    
                    for (const pattern of addressPatterns) {
                        const matches = pageText.match(pattern);
                        if (matches && matches.length > 0) {
                            // Get the first clean match
                            details.detected_address = matches[0].trim().replace(/\\s+/g, ' ');
                            break;
                        }
                    }
                    
                    // Extract EventON structured location
                    const structuredMatch = pageText.match(/LokacijaGradski\\s+[^,\\n]+,\\s*[^,\\n]+,\\s*Varaždin/gi);
                    if (structuredMatch) {
                        details.structured_location = structuredMatch[0].replace('Lokacija', '').trim();
                    }
                    
                    // Extract Varaždin city information
                    if (pageText.includes('Varaždin')) {
                        details.city = 'Varaždin';
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

    async def scrape_with_playwright(self, start_url: str = "https://visitvarazdin.hr/events", max_pages: int = 5, fetch_details: bool = False) -> List[Dict]:
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
                    print(f"Navigating to {start_url}")
                    await page.goto(start_url, wait_until="domcontentloaded", timeout=30000)
                    await page.wait_for_timeout(3000)
                    
                    # Handle cookie consent if present
                    try:
                        cookie_button = await page.query_selector('button')
                        if cookie_button:
                            await cookie_button.click()
                            await page.wait_for_timeout(1000)
                    except:
                        pass
                    
                    page_count = 0
                    current_url = start_url
                    
                    while current_url and page_count < max_pages:
                        page_count += 1
                        print(f"Scraping page {page_count}...")
                        
                        if page_count > 1:
                            await page.goto(current_url, wait_until="domcontentloaded", timeout=30000)
                            await page.wait_for_timeout(3000)
                        
                        # Extract events from current page
                        events_data = await page.evaluate("""
                            () => {
                                const events = [];
                                
                                // Look for event links and information
                                const eventLinks = Array.from(document.querySelectorAll('a[href*="/events/"]'));
                                
                                eventLinks.forEach((link, index) => {
                                    if (index >= 20) return; // Limit to prevent too many results
                                    
                                    const data = {};
                                    
                                    // Extract link
                                    if (link.href) {
                                        data.link = link.href;
                                    }
                                    
                                    // Extract title from link text or nearby elements
                                    const titleText = link.textContent.trim();
                                    if (titleText && titleText.length > 5) {
                                        // Clean up title from EventON format
                                        const cleanTitle = titleText.replace(/\\d{2}\\w{3}.*?\\d{2}:\\d{2}/g, '').trim();
                                        if (cleanTitle) {
                                            data.title = cleanTitle;
                                        }
                                    }
                                    
                                    // Extract image from nearby img elements
                                    const imgEl = link.querySelector('img') || link.parentElement.querySelector('img');
                                    if (imgEl && imgEl.src) {
                                        data.image_url = imgEl.src;
                                    }
                                    
                                    // Extract date information
                                    const dateMatch = link.textContent.match(/\\d{2}\\w{3}/);
                                    if (dateMatch) {
                                        data.date = dateMatch[0];
                                    }
                                    
                                    // Extract time information
                                    const timeMatch = link.textContent.match(/\\d{2}:\\d{2}/);
                                    if (timeMatch) {
                                        data.time = timeMatch[0];
                                    }
                                    
                                    // Extract location from link text (EventON format includes venue)
                                    const locationMatch = link.textContent.match(/([A-ZČĆĐŠŽ][^,\\n]+(?:,\\s*[^,\\n]+)*)/);
                                    if (locationMatch) {
                                        data.location = locationMatch[1].trim();
                                    }
                                    
                                    // Store full text for further processing
                                    data.full_text = link.textContent;
                                    
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
                            next_link = await page.query_selector('a[rel="next"], a.next, .pagination-next a')
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


class VisitVarazdinScraper:
    """High level scraper for VisitVarazdin.hr."""

    def __init__(self) -> None:
        self.requests_scraper = VisitVarazdinRequestsScraper()
        self.playwright_scraper = VisitVarazdinPlaywrightScraper()
        self.transformer = VisitVarazdinDataTransformer()

    async def scrape_events(self, max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> List[EventCreate]:
        """Scrape events from VisitVarazdin.hr with optional enhanced address extraction."""
        raw_events = []
        
        if use_playwright:
            # Try Playwright first for enhanced extraction
            print("Using Playwright for enhanced scraping...")
            try:
                raw_events = await self.playwright_scraper.scrape_with_playwright(
                    start_url="https://visitvarazdin.hr/events", 
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
                raw_events = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
                print(f"Requests approach extracted {len(raw_events)} raw events")
            except Exception as e:
                print(f"Requests approach also failed: {e}")
                raw_events = []
            finally:
                await self.requests_scraper.close()
        
        # Transform raw data to EventCreate objects
        events: List[EventCreate] = []
        for item in raw_events:
            event = self.transformer.transform(item)
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


async def scrape_visitvarazdin_events(max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> Dict:
    """Scrape VisitVarazdin.hr events with optional enhanced address extraction."""
    scraper = VisitVarazdinScraper()
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
            "message": f"Scraped {len(events)} events from VisitVarazdin.hr, saved {saved} new events" + 
                      (f" (with enhanced address extraction)" if use_playwright else ""),
        }
    except Exception as e:
        return {"status": "error", "message": f"VisitVarazdin scraping failed: {e}"}
