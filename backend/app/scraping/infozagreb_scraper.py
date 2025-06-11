"""InfoZagreb.hr events scraper."""

from __future__ import annotations

import asyncio
import re
from datetime import date
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag
import os

from ..models.schemas import EventCreate

BASE_URL = "https://www.infozagreb.hr"
EVENTS_URL = f"{BASE_URL}/en/events"

HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0",
}

# BrightData configuration (shared with other scrapers)
USER = os.getenv("BRIGHTDATA_USER", "demo_user")
PASSWORD = os.getenv("BRIGHTDATA_PASSWORD", "demo_password")
BRIGHTDATA_HOST_RES = "brd.superproxy.io"
BRIGHTDATA_PORT = int(os.getenv("BRIGHTDATA_PORT", 22225))
SCRAPING_BROWSER_EP = f"https://brd.superproxy.io:{BRIGHTDATA_PORT}"
PROXY = f"http://{USER}:{PASSWORD}@{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"
BRD_WSS = f"wss://{USER}:{PASSWORD}@brd.superproxy.io:9222"

USE_SB = os.getenv("USE_SCRAPING_BROWSER", "0") == "1"
USE_PROXY = os.getenv("USE_PROXY", "0") == "1"
USE_PLAYWRIGHT = os.getenv("USE_PLAYWRIGHT", "1") == "1"


class InfoZagrebEventDataTransformer:
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
        """Parse a variety of date formats commonly found on InfoZagreb."""
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
                        month_num = InfoZagrebEventDataTransformer.CRO_MONTHS.get(month.lower())
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
        """Return time in HH:MM format."""
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
            name = cls.clean_text(data.get("title", ""))
            location = cls.clean_text(data.get("location", "Zagreb"))
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
                location=location or "Zagreb",
                description=description or f"Event: {name}",
                price=price or "Check website",
                image=image,
                link=link,
            )
        except Exception:
            return None


class InfoZagrebRequestsScraper:
    """Scraper using httpx and BeautifulSoup."""

    def __init__(self) -> None:
        pass

    async def fetch(self, url: str) -> httpx.Response:
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
            print(f"Request failed for {url}: {e}")
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

        loc_el = soup.select_one(".location, .venue, .place")
        if loc_el:
            data["location"] = loc_el.get_text(strip=True)

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
        pass


class InfoZagrebPlaywrightScraper:
    """Scraper using Playwright and optional BrightData proxy."""

    async def scrape_with_playwright(
        self, start_url: str = EVENTS_URL, max_pages: int = 5
    ) -> List[Dict]:
        from playwright.async_api import async_playwright

        all_events: List[Dict] = []
        page_count = 0

        async with async_playwright() as p:
            if USE_PROXY:
                browser = await p.chromium.connect_over_cdp(BRD_WSS)
            else:
                browser = await p.chromium.launch()

            page = await browser.new_page()

            current_url = start_url

            try:
                while current_url and page_count < max_pages:
                    await page.goto(current_url, wait_until="domcontentloaded", timeout=90000)
                    await page.wait_for_timeout(3000)

                    events_data = await page.evaluate(
                        """
                        () => {
                            const events = [];
                            const selectors = ['li.event-item','div.event-item','article','.events-list li'];
                            let containers = [];
                            for (const sel of selectors) {
                                const found = document.querySelectorAll(sel);
                                if (found.length) { containers = Array.from(found); break; }
                            }
                            containers.forEach(el => {
                                const data = {};
                                const linkEl = el.querySelector('a');
                                if (linkEl && linkEl.href) {
                                    data.link = linkEl.href;
                                    data.title = linkEl.textContent.trim();
                                }
                                const dateEl = el.querySelector('.date, time');
                                if (dateEl) data.date = dateEl.textContent.trim();
                                const imgEl = el.querySelector('img');
                                if (imgEl) data.image = imgEl.src || imgEl.getAttribute('data-src');
                                const locEl = el.querySelector('.location, .venue, .place');
                                if (locEl) data.location = locEl.textContent.trim();
                                if (Object.keys(data).length) events.push(data);
                            });
                            return events;
                        }
                        """
                    )

                    all_events.extend(events_data)

                    next_url = await page.evaluate(
                        """
                        () => {
                            const link = document.querySelector('a[rel="next"], .pagination-next a, a.next');
                            return link ? link.href : null;
                        }
                        """
                    )

                    if next_url:
                        current_url = next_url
                        page_count += 1
                    else:
                        break

                    await page.wait_for_timeout(1000)
            finally:
                await browser.close()

        return all_events


class InfoZagrebScraper:
    """High level scraper for InfoZagreb.hr."""

    def __init__(self) -> None:
        self.requests_scraper = InfoZagrebRequestsScraper()
        self.playwright_scraper = InfoZagrebPlaywrightScraper()
        self.transformer = InfoZagrebEventDataTransformer()

    async def scrape_events(
        self, max_pages: int = 5, use_playwright: bool | None = None
    ) -> List[EventCreate]:
        if use_playwright is None:
            use_playwright = USE_PLAYWRIGHT

        if use_playwright:
            raw = await self.playwright_scraper.scrape_with_playwright(
                max_pages=max_pages
            )
        else:
            raw = await self.requests_scraper.scrape_all_events(max_pages=max_pages)

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


async def scrape_infozagreb_events(max_pages: int = 5) -> Dict:
    scraper = InfoZagrebScraper()
    try:
        events = await scraper.scrape_events(max_pages=max_pages)
        saved = scraper.save_events_to_database(events)
        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved,
            "message": f"Scraped {len(events)} events from InfoZagreb.hr, saved {saved} new events",
        }
    except Exception as e:
        return {"status": "error", "message": f"InfoZagreb scraping failed: {e}"}

