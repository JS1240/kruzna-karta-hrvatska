"""Zadar.travel events scraper using Bright Data proxy support."""

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
from ..core.database import SessionLocal
from ..models.event import Event

# BrightData configuration (same as other scrapers)
USER = os.getenv("BRIGHTDATA_USER", "demo_user")
PASSWORD = os.getenv("BRIGHTDATA_PASSWORD", "demo_password")
BRIGHTDATA_HOST_RES = "brd.superproxy.io"
BRIGHTDATA_PORT = int(os.getenv("BRIGHTDATA_PORT", 22225))
PROXY = f"http://{USER}:{PASSWORD}@{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"

USE_PROXY = os.getenv("USE_PROXY", "0") == "1"

BASE_URL = "https://zadar.travel"
EVENTS_URL = f"{BASE_URL}/hr/dogadanja"

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0",
}


class ZadarEventDataTransformer:
    """Transform raw Zadar event data to :class:`EventCreate`."""

    CRO_MONTHS = {
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
    }

    @staticmethod
    def clean_text(text: str) -> str:
        return " ".join(text.split()) if text else ""

    @classmethod
    def parse_date(cls, date_str: str) -> Optional[date]:
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
                    if pattern.startswith("(\\d{1,2})\\."):
                        d, mth, y = m.groups()
                        return date(int(y), int(mth), int(d))
                    elif pattern.startswith("(\\d{4})"):
                        y, mth, d = m.groups()
                        return date(int(y), int(mth), int(d))
                    else:
                        d, month_name, y = m.groups()
                        month_num = cls.CRO_MONTHS.get(month_name.lower())
                        if month_num:
                            return date(int(y), month_num, int(d))
                except Exception:
                    continue
        year = re.search(r"(\d{4})", date_str)
        if year:
            try:
                return date(int(year.group(1)), 1, 1)
            except ValueError:
                pass
        return None

    @staticmethod
    def parse_time(time_str: str) -> str:
        if not time_str:
            return "20:00"
        m = re.search(r"(\d{1,2}):(\d{2})", time_str)
        if m:
            h, minute = m.groups()
            return f"{int(h):02d}:{minute}"
        m = re.search(r"(\d{1,2})h", time_str)
        if m:
            h = m.group(1)
            return f"{int(h):02d}:00"
        return "20:00"

    @classmethod
    def transform(cls, data: Dict) -> Optional[EventCreate]:
        try:
            name = cls.clean_text(data.get("title", ""))
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

            if not name or len(name) < 3:
                return None

            return EventCreate(
                name=name,
                time=parsed_time,
                date=parsed_date,
                location=location or "Zadar",
                description=description or f"Event: {name}",
                price=price or "Check website",
                image=image,
                link=link,
            )
        except Exception:
            return None


class ZadarRequestsScraper:
    """Scraper using httpx and BeautifulSoup."""

    def __init__(self) -> None:
        proxies = {"http": PROXY, "https": PROXY} if USE_PROXY else None
        self.client = httpx.AsyncClient(headers=HEADERS, proxies=proxies, verify=False)

    async def fetch(self, url: str) -> httpx.Response:
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

        desc_el = soup.select_one(".description, .text, article, .entry-content")
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

        price_el = soup.find(string=re.compile("EUR|HRK|free", re.IGNORECASE))
        if price_el:
            data["price"] = price_el.strip()

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

        return data

    async def scrape_events_page(self, url: str) -> Tuple[List[Dict], Optional[str]]:
        resp = await self.fetch(url)
        soup = BeautifulSoup(resp.text, "html.parser")

        events: List[Dict] = []
        containers = []
        selectors = [
            "li.event-item",
            "div.event-item",
            "article",
            ".events-list li",
        ]
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


class ZadarScraper:
    """High level scraper for Zadar.travel."""

    def __init__(self) -> None:
        self.requests_scraper = ZadarRequestsScraper()
        self.transformer = ZadarEventDataTransformer()

    async def scrape_events(self, max_pages: int = 5) -> List[EventCreate]:
        raw = await self.requests_scraper.scrape_all_events(max_pages=max_pages)
        events: List[EventCreate] = []
        for item in raw:
            event = self.transformer.transform(item)
            if event:
                events.append(event)
        await self.requests_scraper.close()
        return events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        if not events:
            return 0
        db = SessionLocal()
        try:
            saved = 0
            for ev in events:
                existing = (
                    db.query(Event)
                    .filter(Event.name == ev.name, Event.date == ev.date)
                    .first()
                )
                if not existing:
                    db_event = Event(**ev.model_dump())
                    db.add(db_event)
                    saved += 1
            db.commit()
            return saved
        except Exception:
            db.rollback()
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
            "message": f"Scraped {len(events)} events from Zadar.travel, saved {saved} new events",
        }
    except Exception as e:
        return {"status": "error", "message": f"Zadar.travel scraping failed: {e}"}
