"""Ulaznice.hr event scraper with BrightData proxy support."""

import asyncio
import os
import re
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
import requests
from bs4 import BeautifulSoup, Tag
from sqlalchemy.dialects.postgresql import insert

from ..core.database import SessionLocal
from ..models.event import Event
from ..models.schemas import EventCreate

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
    def transform_to_event_create(scraped: Dict) -> Optional[EventCreate]:
        try:
            name = UlazniceDataTransformer.clean_text(scraped.get("title", ""))
            if not name or len(name) < 3:
                return None
            location = UlazniceDataTransformer.clean_text(scraped.get("venue", ""))
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
                name=name,
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
    """Scraper for https://www.ulaznice.hr/web/events"""

    def __init__(self) -> None:
        self.session = requests.Session()

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
            print(f"Request failed for {url}: {e}")
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
            print(f"Request failed for {url}: {e}")
            raise

    def parse_event_from_element(self, elem: Tag) -> Dict:
        data: Dict[str, str] = {}
        try:
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
            title_el = elem.select_one(".title, .event-title, h3, h2")
            if title_el:
                data["title"] = title_el.get_text(strip=True)
            date_el = elem.select_one(".date, time")
            if date_el:
                data["date"] = date_el.get_text(strip=True)
            venue_el = elem.select_one(".venue, .location")
            if venue_el:
                data["venue"] = venue_el.get_text(strip=True)
            price_el = elem.select_one(".price")
            if price_el:
                data["price"] = price_el.get_text(strip=True)
        except Exception as e:
            print(f"Error parsing element: {e}")
        return data

    async def scrape_events_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        print(f"Fetching {url}")
        resp = await self.fetch_async(url)
        soup = BeautifulSoup(resp.text, "html.parser")
        events: List[Dict] = []

        selectors = ["div.event", "div.card", "article"]
        event_elements: List[Tag] = []
        for sel in selectors:
            event_elements = soup.select(sel)
            if event_elements:
                break
        for elem in event_elements:
            if isinstance(elem, Tag):
                event_data = self.parse_event_from_element(elem)
                if event_data:
                    events.append(event_data)

        next_page_url = None
        next_link = soup.select_one('a[rel="next"], a.next')
        if next_link and isinstance(next_link, Tag):
            href = next_link.get("href")
            if href:
                next_page_url = urljoin(url, href)

        return events, next_page_url

    async def scrape_events(
        self, start_url: str = "https://www.ulaznice.hr/web/events", max_pages: int = 5
    ) -> List[EventCreate]:
        all_events: List[EventCreate] = []
        current_url = start_url
        pages = 0

        while current_url and pages < max_pages:
            try:
                events_data, next_url = await self.scrape_events_page(current_url)
                for ev in events_data:
                    ec = UlazniceDataTransformer.transform_to_event_create(ev)
                    if ec:
                        all_events.append(ec)
                pages += 1
                current_url = next_url
                await asyncio.sleep(1)
            except Exception as e:
                print(f"Failed to scrape {current_url}: {e}")
                break

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
                    .returning(Event.name, Event.date)
                    .on_conflict_do_nothing()
                ).fetchall()
            )
            to_insert = [
                e for e in event_dicts if (e["name"], e["date"]) not in existing_pairs
            ]
            if to_insert:
                stmt = insert(Event).values(to_insert)
                stmt = stmt.on_conflict_do_nothing(index_elements=["name", "date"])
                db.execute(stmt)
                db.commit()
                return len(to_insert)
            db.commit()
            return 0
        except Exception as e:
            print(f"Error saving events: {e}")
            db.rollback()
            raise
        finally:
            db.close()


async def scrape_ulaznice_events(max_pages: int = 5) -> Dict:
    """Scrape Ulaznice.hr events and save to database."""
    scraper = UlazniceScraper()
    try:
        events = await scraper.scrape_events(max_pages=max_pages)
        saved = scraper.save_events_to_database(events)
        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved,
            "message": f"Successfully scraped {len(events)} events, saved {saved} new events",
        }
    except Exception as e:
        return {"status": "error", "message": f"Ulaznice.hr scraping failed: {e}"}
