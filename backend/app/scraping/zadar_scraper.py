"""Zadar Travel events scraper with optional Bright Data proxy."""

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

    @classmethod
    def transform(cls, data: Dict) -> Optional[EventCreate]:
        try:
            title = cls.clean_text(data.get("title", ""))
            location = cls.clean_text(data.get("location", "Zadar"))
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
                    # Default to Zadar if location is generic or empty
                    if location_text and location_text.lower() not in ["", "zadar"]:
                        data["location"] = f"{location_text}, Zadar"
                    else:
                        data["location"] = "Zadar"
                    break
        
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
            print("Detected Nuxt.js SPA - static HTML has no events content")
            print("Playwright is required to scrape events from this JavaScript application")
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
                        print(f"Warning: Could not fetch details from {link}: {e}")
                
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
        
        print(f"Starting Zadar scraper from {EVENTS_URL}")
        
        while current_url and page < max_pages:
            page += 1
            print(f"Scraping page {page}: {current_url}")
            
            try:
                events, next_url = await self.scrape_events_page(current_url)
                print(f"Found {len(events)} events on page {page}")
                all_events.extend(events)
                
                if not next_url or not events:
                    print(f"No more pages or events found after page {page}")
                    break
                    
                current_url = next_url
                await asyncio.sleep(1)  # Be respectful
                
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                break
        
        print(f"Total events scraped: {len(all_events)}")
        return all_events

    async def close(self) -> None:
        await self.client.aclose()


class ZadarPlaywrightScraper:
    """Playwright scraper for JavaScript-heavy Zadar Travel website."""
    
    async def scrape_with_playwright(self, max_pages: int = 5) -> List[Dict]:
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
                    print(f"Navigating to {EVENTS_URL}")
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
                                            data.location = locText === 'Zadar' ? 'Zadar' : `${locText}, Zadar`;
                                        }
                                    }
                                });
                                
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
                    
                    print(f"Found {len(events_data)} events via Playwright")
                    all_events.extend(events_data)
                    
                except Exception as e:
                    print(f"Error scraping with Playwright: {e}")
                
                await browser.close()
            
            return all_events
            
        except ImportError:
            print("Playwright not available, falling back to requests approach")
            return []
        except Exception as e:
            print(f"Playwright error: {e}")
            return []


class ZadarScraper:
    """High level scraper for Zadar Travel."""

    def __init__(self) -> None:
        self.requests_scraper = ZadarRequestsScraper()
        self.playwright_scraper = ZadarPlaywrightScraper()
        self.transformer = ZadarTransformer()

    async def scrape_events(self, max_pages: int = 5, use_playwright: bool = True) -> List[EventCreate]:
        raw = []
        
        if use_playwright:
            # Try Playwright first for JavaScript-heavy content
            raw = await self.playwright_scraper.scrape_with_playwright(max_pages=max_pages)
            
            # If Playwright fails or returns no results, fallback to requests
            if not raw:
                print("Playwright returned no results, falling back to requests approach")
                raw = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
                await self.requests_scraper.close()
        else:
            # Use requests approach directly
            raw = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
            await self.requests_scraper.close()
        
        events: List[EventCreate] = []
        for item in raw:
            event = self.transformer.transform(item)
            if event:
                events.append(event)
        
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
                        print(f"Skipping event {event_data.get('title', 'Unknown')}: {e}")
                        continue
                
                db.commit()
                return saved_count
            db.commit()
            return 0
        except Exception as e:
            db.rollback()
            print(f"Database error in Zadar scraper: {e}")
            raise
        finally:
            db.close()


async def scrape_zadar_events(max_pages: int = 5) -> Dict:
    scraper = ZadarScraper()
    try:
        events = await scraper.scrape_events(max_pages=max_pages)
        saved = scraper.save_events_to_database(events)
        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved,
            "message": f"Scraped {len(events)} events from Zadar Travel, saved {saved} new events",
        }
    except Exception as e:
        return {"status": "error", "message": f"Zadar scraping failed: {e}"}
