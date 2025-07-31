"""Zadar Travel events scraper with optional Bright Data proxy."""

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

# Set up logging
logger = logging.getLogger(__name__)
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

BASE_URL = "https://zadar.travel"
EVENTS_URL = f"{BASE_URL}/events/"


class ZadarTransformer:
    """Transform raw Zadar Travel event data to :class:`EventCreate`."""

    CRO_MONTHS = {
        "siječanj": 1,
        "veljača": 2,
        "ožujak": 3,
        "travanj": 4,
        "svibanj": 5,
        "lipanj": 6,
        "srpanj": 7,
        "kolovoz": 8,
        "rujan": 9,
        "listopad": 10,
        "studeni": 11,
        "prosinac": 12,
        # English fallbacks
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
        
        # Handle date ranges - extract the first date
        # Format: "27.12.2025. - 27.12.2025." or "01.06.2025. - 05.06.2025."
        range_match = re.search(r"(\d{1,2})\.(\d{1,2})\.(\d{4})\.\s*-", date_str)
        if range_match:
            day, month, year = range_match.groups()
            try:
                return date(int(year), int(month), int(day))
            except (ValueError, TypeError):
                pass
        
        patterns = [
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})",  # DD.MM.YYYY
            r"(\d{4})-(\d{1,2})-(\d{1,2})",   # YYYY-MM-DD
            r"(\d{1,2})\s+(\w+)\s*(\d{4})",   # DD Month YYYY
        ]
        for pattern in patterns:
            m = re.search(pattern, date_str, re.IGNORECASE)
            if m:
                try:
                    if pattern.startswith(r"(\d{1,2})\."):
                        day, month, year = m.groups()
                        if month.isdigit():
                            return date(int(year), int(month), int(day))
                        month_num = ZadarTransformer.CRO_MONTHS.get(month.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                    elif pattern.startswith(r"(\d{4})"):
                        year, month, day = m.groups()
                        return date(int(year), int(month), int(day))
                    else:  # Month name format
                        day, month_name, year = m.groups()
                        month_num = ZadarTransformer.CRO_MONTHS.get(month_name.lower())
                        if month_num:
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
        """Extract and format location from Zadar event data with enhanced address support."""
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
        
        # Fallback to Zadar if nothing found
        return location if location else "Zadar"

    @staticmethod
    def parse_location_from_text(text: str) -> Dict[str, str]:
        """Parse location information from event text using Zadar-specific patterns."""
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
        
        # Pattern 3: Enhanced Croatian address patterns for Zadar region
        address_patterns = [
            # Full address with postal code: "Ulica Vladimira Nazora 1, 23000 Zadar"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,?\s*23000\s+Zadar)",
            # Street with number: "Ulica Vladimira Nazora 1", "Trg pet bunara 5"
            r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+(?:trg|ulica|ul\.|cesta)?\s*\d+[a-z]?)",
            # Postal code with city: "23000 Zadar"
            r"(23000\s+Zadar(?:[^\n,]*)?)",
            # Zadar-specific venue patterns
            r"((?:Cedulin Palace|Church of St|Zadar City Walls|City Library|Tourist)\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]*)",
            # General Croatian address with number (broader pattern)
            r"([A-ZČĆĐŠŽ][a-zčćđšž]{2,}\s+(?:[A-ZČĆĐŠŽ][a-zčćđšž\s]*\s+)?\d+[a-z]?)"
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                result["detected_address"] = matches[0].strip()
                break
        
        # Extract Zadar city information
        if "Zadar" in text:
            result["city"] = "Zadar"
        
        return result

    @staticmethod
    def get_zadar_venues():
        """Get list of known Zadar venues for enhanced recognition."""
        return [
            "Cedulin Palace Atrium",
            "Church of St Chrysogonus", 
            "Zadar City Walls",
            "City Library Zadar",
            "Arsenal Zadar",
            "Forum Zadar",
            "Sea Organ",
            "Greeting to the Sun",
            "Five Wells Square",
            "People's Square",
            "St. Donatus Church",
            "Archaeological Museum Zadar",
            "Museum of Ancient Glass",
            "Tourist Information Centre Zadar"
        ]

    @classmethod
    def transform(cls, data: Dict) -> Optional[EventCreate]:
        try:
            title = cls.clean_text(data.get("title", ""))
            
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

            if not title or len(title) < 3:
                return None

            return EventCreate(
                title=title,  # Changed from 'name' to 'title'
                time=parsed_time,
                date=parsed_date,
                location=location or "Zadar",
                description=description or f"Event: {title}",
                price=price or "Contact organizer",
                image=image,
                link=link,
                source="manual",  # Use allowed source value
            )
        except Exception:
            return None


class ZadarRequestsScraper:
    """Scraper using httpx and BeautifulSoup with optional Bright Data proxy."""

    def __init__(self) -> None:
        self.client = httpx.AsyncClient(headers=HEADERS)

    async def fetch(self, url: str) -> httpx.Response:
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
        
        # Extract title from h1.a-item__title
        title_el = el.select_one("h1.a-item__title")
        if title_el and title_el.get_text(strip=True):
            data["title"] = title_el.get_text(strip=True)
        
        # Extract image from a.a-item__img img
        img_el = el.select_one("a.a-item__img img")
        if img_el and img_el.get("src"):
            data["image"] = img_el.get("src")
        
        # Extract external link from a.a-item__details__item with icon-link
        link_containers = el.select("a.a-item__details__item")
        for container in link_containers:
            if container.select_one(".icon-link") and container.get("href"):
                data["link"] = container.get("href")  # These are often external URLs
                break
        
        # Extract date from icon-calendar sibling
        date_containers = el.select(".a-item__details__item")
        for container in date_containers:
            if container.select_one(".icon-calendar"):
                date_p = container.select_one("p")
                if date_p and date_p.get_text(strip=True):
                    data["date"] = date_p.get_text(strip=True)
                    break
        
        # Extract location from icon-pin sibling
        location_containers = el.select(".a-item__details__item")
        for container in location_containers:
            if container.select_one(".icon-pin"):
                loc_p = container.select_one("p")
                if loc_p and loc_p.get_text(strip=True):
                    location_text = loc_p.get_text(strip=True)
                    # Store raw location for enhanced processing
                    data["location"] = location_text
                    break
        
        # Capture full element text for pattern matching
        element_text = el.get_text(separator=" ", strip=True)
        if element_text:
            data["full_text"] = element_text
        
        # Fallback for location
        if "location" not in data:
            data["location"] = "Zadar"
        
        # No price info typically available in listing, will try detail page
        return data

    async def scrape_events_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        resp = await self.fetch(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        events: List[Dict] = []
        
        # Look for Vue.js event articles
        containers = soup.select("article.a-item")
        
        # Since this is a JavaScript SPA, the static HTML won't have events
        # The actual events need to be scraped using Playwright when available
        if not containers and "Loading..." in resp.text:
            logger.warning("Detected Nuxt.js SPA - static HTML has no events content")
            logger.warning("Playwright is required to scrape events from this JavaScript application")
            return [], None
        
        # Fallback selectors if Vue.js structure not found
        if not containers:
            fallback_selectors = ["li.event-item", "div.event-item", "article", ".events-list li"]
            for sel in fallback_selectors:
                found = soup.select(sel)
                if found:
                    containers = found
                    break

        for el in containers:
            if isinstance(el, Tag):
                data = self.parse_listing_element(el)
                
                # Try to get more details from individual event page if we have a link
                link = data.get("link")
                if link and link.startswith("http"):  # Only for external links that might have more info
                    try:
                        detail = await self.parse_event_detail(link)
                        # Only update with non-empty values
                        data.update({k: v for k, v in detail.items() if v})
                    except Exception as e:
                        # Log but don't fail the whole scraping
                        logger.warning(f"Warning: Could not fetch details from {link}: {e}")
                
                # Only add events that have at least title and date
                if data.get("title") and data.get("date"):
                    events.append(data)

        # Look for pagination
        next_url = None
        pagination_selectors = [
            'a[rel="next"]', 
            '.pagination-next a', 
            'a.next',
            '.pagination a[aria-label*="Next"]',
            '.pagination a:contains("Next")',
            '.pagination a:contains(">")'
        ]
        
        for selector in pagination_selectors:
            next_link = soup.select_one(selector)
            if next_link and next_link.get("href"):
                next_url = urljoin(url, next_link.get("href"))
                break

        return events, next_url

    async def scrape_all_events(self, max_pages: int = 5) -> List[Dict]:
        all_events: List[Dict] = []
        current_url = EVENTS_URL
        page = 0
        
        logger.info(f"Starting Zadar scraper from {EVENTS_URL}")
        
        while current_url and page < max_pages:
            page += 1
            logger.info(f"Scraping page {page}: {current_url}")
            
            try:
                events, next_url = await self.scrape_events_page(current_url)
                logger.info(f"Found {len(events)} events on page {page}")
                all_events.extend(events)
                
                if not next_url or not events:
                    logger.info(f"No more pages or events found after page {page}")
                    break
                    
                current_url = next_url
                await asyncio.sleep(1)  # Be respectful
                
            except Exception as e:
                logger.error(f"Error scraping page {page}: {e}")
                break
        
        logger.info(f"Total events scraped: {len(all_events)}")
        return all_events

    async def close(self) -> None:
        await self.client.aclose()


class ZadarPlaywrightScraper:
    """Playwright scraper for JavaScript-heavy Zadar Travel website."""
    
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
                        // Full address: "Ulica Vladimira Nazora 1, 23000 Zadar"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+\\d+[a-z]?\\s*,?\\s*23000\\s+Zadar)/gi,
                        // Street with number: "Ulica Vladimira Nazora 1", "Trg pet bunara 5"
                        /([A-ZČĆĐŠŽ][a-zčćđšž\\s]+\\s+(?:trg|ulica|ul\\.|cesta)?\\s*\\d+[a-z]?)/gi,
                        // Postal code + city: "23000 Zadar"
                        /(23000\\s+Zadar(?:[^\\n,]*)?)/gi,
                        // Zadar-specific venues
                        /(Cedulin Palace|Church of St|Zadar City Walls|City Library|Arsenal|Forum|Sea Organ)/gi
                    ];
                    
                    for (const pattern of addressPatterns) {
                        const matches = pageText.match(pattern);
                        if (matches && matches.length > 0) {
                            // Get the first clean match
                            details.detected_address = matches[0].trim().replace(/\\s+/g, ' ');
                            break;
                        }
                    }
                    
                    // Extract Zadar city information
                    if (pageText.includes('Zadar')) {
                        details.city = 'Zadar';
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
    
    async def scrape_with_playwright(self, max_pages: int = 5, fetch_details: bool = False) -> List[Dict]:
        try:
            from playwright.async_api import async_playwright
            import random
            
            all_events = []
            
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-web-security',
                    ]
                )
                
                # Create context with realistic settings
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='hr-HR',
                    timezone_id='Europe/Zagreb',
                )
                
                page = await context.new_page()
                
                try:
                    logger.info(f"Navigating to {EVENTS_URL}")
                    await page.goto(EVENTS_URL, wait_until="networkidle", timeout=30000)
                    
                    # Wait for content to load
                    await page.wait_for_timeout(5000)
                    
                    # Extract events using JavaScript
                    events_data = await page.evaluate("""
                        () => {
                            const events = [];
                            
                            // Look for Vue.js event articles
                            const articles = document.querySelectorAll('article.a-item');
                            console.log(`Found ${articles.length} event articles`);
                            
                            articles.forEach(article => {
                                const data = {};
                                
                                // Extract title
                                const titleEl = article.querySelector('h1.a-item__title');
                                if (titleEl) {
                                    data.title = titleEl.textContent?.trim() || '';
                                }
                                
                                // Extract image
                                const imgEl = article.querySelector('a.a-item__img img');
                                if (imgEl) {
                                    data.image = imgEl.src || '';
                                }
                                
                                // Extract external link
                                const linkEls = article.querySelectorAll('a.a-item__details__item');
                                linkEls.forEach(linkEl => {
                                    if (linkEl.querySelector('.icon-link') && linkEl.href) {
                                        data.link = linkEl.href;
                                    }
                                });
                                
                                // Extract date
                                const detailItems = article.querySelectorAll('.a-item__details__item');
                                detailItems.forEach(item => {
                                    if (item.querySelector('.icon-calendar')) {
                                        const dateP = item.querySelector('p');
                                        if (dateP) {
                                            data.date = dateP.textContent?.trim() || '';
                                        }
                                    }
                                    
                                    // Extract location
                                    if (item.querySelector('.icon-pin')) {
                                        const locP = item.querySelector('p');
                                        if (locP) {
                                            const locText = locP.textContent?.trim() || '';
                                            data.location = locText;
                                        }
                                    }
                                });
                                
                                // Store full article text for enhanced processing
                                data.full_text = article.textContent;
                                
                                // Default location fallback
                                if (!data.location) {
                                    data.location = 'Zadar';
                                }
                                
                                // Only add events with title and date
                                if (data.title && data.date) {
                                    events.push(data);
                                }
                            });
                            
                            return events;
                        }
                    """)
                    
                    valid_events = [
                        event for event in events_data
                        if event.get("title") and event.get("date")
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
                    
                    logger.info(f"Found {len(valid_events)} events via Playwright")
                    all_events.extend(valid_events)
                    
                except Exception as e:
                    logger.error(f"Error scraping with Playwright: {e}")
                
                await browser.close()
            
            return all_events
            
        except ImportError:
            logger.warning("Playwright not available, falling back to requests approach")
            return []
        except Exception as e:
            logger.error(f"Playwright error: {e}")
            return []


class ZadarScraper:
    """High level scraper for Zadar Travel."""

    def __init__(self) -> None:
        self.requests_scraper = ZadarRequestsScraper()
        self.playwright_scraper = ZadarPlaywrightScraper()
        self.transformer = ZadarTransformer()

    async def scrape_events(self, max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> List[EventCreate]:
        raw = []
        
        if use_playwright:
            # Try Playwright first for JavaScript-heavy content
            logger.info("Using Playwright for enhanced scraping...")
            try:
                raw = await self.playwright_scraper.scrape_with_playwright(
                    max_pages=max_pages, 
                    fetch_details=fetch_details
                )
                logger.info(f"Playwright extracted {len(raw)} raw events")
            except Exception as e:
                logger.error(f"Playwright failed: {e}, falling back to requests approach")
                raw = []
            
            # If Playwright fails or returns no results, fallback to requests
            if not raw:
                logger.warning("Playwright returned no results, falling back to requests approach")
                raw = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
                await self.requests_scraper.close()
        else:
            # Use requests approach directly
            logger.info("Using requests/BeautifulSoup approach...")
            raw = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
            await self.requests_scraper.close()
        
        events: List[EventCreate] = []
        for item in raw:
            event = self.transformer.transform(item)
            if event:
                events.append(event)
        
        logger.info(f"Transformed {len(events)} valid events from {len(raw)} raw events")
        return events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        from sqlalchemy import select, tuple_

        from backend.app.core.database import SessionLocal
        from backend.app.models.event import Event

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
                # Insert each event individually to handle any constraint issues
                saved_count = 0
                for event_data in to_insert:
                    try:
                        event = Event(**event_data)
                        db.add(event)
                        db.flush()  # Get the ID without committing
                        saved_count += 1
                    except Exception as e:
                        # Skip duplicate or invalid events
                        db.rollback()
                        logger.warning(f"Skipping event {event_data.get('title', 'Unknown')}: {e}")
                        continue
                
                db.commit()
                return saved_count
            db.commit()
            return 0
        except Exception as e:
            db.rollback()
            logger.error(f"Database error in Zadar scraper: {e}")
            raise
        finally:
            db.close()


async def scrape_zadar_events(max_pages: int = 5, use_playwright: bool = True, fetch_details: bool = False) -> Dict:
    scraper = ZadarScraper()
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
            "message": f"Scraped {len(events)} events from Zadar Travel, saved {saved} new events" + 
                      (" (with enhanced address extraction)" if use_playwright else ""),
        }
    except Exception as e:
        return {"status": "error", "message": f"Zadar scraping failed: {e}"}
