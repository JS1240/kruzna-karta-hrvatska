"""Refactored VisitRijeka.hr events scraper using BaseScraper."""

from __future__ import annotations

import re
from datetime import date
from typing import Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from ..models.schemas import EventCreate
from .base_scraper import BaseScraper, CROATIAN_MONTHS


class VisitRijekaScraper(BaseScraper):
    """Scraper for VisitRijeka.hr events using the base scraper infrastructure."""

    def __init__(self):
        super().__init__(
            base_url="https://visitrijeka.hr",
            events_url="https://visitrijeka.hr/en/events",
            source_name="visitrijeka"
        )

    def _find_event_containers(self, soup: BeautifulSoup) -> List[Tag]:
        """Find event container elements on the page."""
        selectors = ["li.event-item", "div.event-item", "article", ".events-list li"]
        
        for selector in selectors:
            containers = soup.select(selector)
            if containers:
                return containers
        
        return []

    def parse_listing_element(self, element: Tag) -> Dict[str, str]:
        """Parse event information from listing page element."""
        data = {}
        
        # Extract link and title
        link_el = element.select_one("a")
        if link_el and link_el.get("href"):
            data["link"] = urljoin(self.base_url, link_el.get("href"))
            if link_el.get_text(strip=True):
                data["title"] = link_el.get_text(strip=True)

        # Extract date
        date_el = element.select_one(".date, time")
        if date_el and date_el.get_text(strip=True):
            data["date"] = date_el.get_text(strip=True)

        # Extract image
        img_el = element.select_one("img")
        if img_el and img_el.get("src"):
            data["image"] = img_el.get("src")

        # Extract location
        loc_el = element.select_one(".location, .venue, .place")
        if loc_el:
            data["location"] = loc_el.get_text(strip=True)

        # Extract price
        price_el = element.select_one(".price")
        if price_el:
            data["price"] = price_el.get_text(strip=True)

        return data

    async def parse_event_detail(self, url: str) -> Dict[str, str]:
        """Parse detailed event information from event page."""
        response = await self.fetch_with_retry(url)
        soup = BeautifulSoup(response.text, "html.parser")
        data = {}

        # Extract title
        title_el = soup.select_one("h1")
        if title_el:
            data["title"] = title_el.get_text(strip=True)

        # Extract description
        desc_el = soup.select_one(".description, .text, article")
        if desc_el:
            data["description"] = desc_el.get_text(separator=" ", strip=True)

        # Extract date from page content
        date_el = soup.find(string=re.compile(r"\d{4}"))
        if date_el:
            data["date"] = date_el.strip()

        # Extract time
        time_el = soup.find(string=re.compile(r"\d{1,2}:\d{2}"))
        if time_el:
            data["time"] = time_el.strip()

        # Extract image
        img_el = soup.select_one("img[src]")
        if img_el:
            data["image"] = img_el.get("src")

        # Extract location
        loc_el = soup.select_one(".location, .venue, .place")
        if loc_el:
            data["location"] = loc_el.get_text(strip=True)

        # Extract price
        price_el = soup.select_one(".price")
        if price_el:
            data["price"] = price_el.get_text(strip=True)

        return data

    def transform_to_event(self, raw_data: Dict[str, str]) -> Optional[EventCreate]:
        """Transform raw scraped data to EventCreate object."""
        try:
            name = self.clean_text(raw_data.get("title", ""))
            location = self.clean_text(raw_data.get("location", "Rijeka"))
            description = self.clean_text(raw_data.get("description", ""))
            price = self.clean_text(raw_data.get("price", ""))

            # Parse date
            date_str = raw_data.get("date", "")
            parsed_date = self.parse_date(date_str)
            if not parsed_date:
                return None

            # Parse time
            time_str = raw_data.get("time", "")
            parsed_time = self.parse_time(time_str)

            # Handle image URL
            image = raw_data.get("image")
            if image and not image.startswith("http"):
                image = urljoin(self.base_url, image)

            # Handle link URL
            link = raw_data.get("link")
            if link and not link.startswith("http"):
                link = urljoin(self.base_url, link)

            # Validate minimum requirements
            if not name or len(name) < 3:
                return None

            return EventCreate(
                name=name,
                time=parsed_time,
                date=parsed_date,
                location=location or "Rijeka",
                description=description or f"Event: {name}",
                price=price or "Check website",
                image=image,
                link=link,
                source=self.source_name
            )
        except Exception:
            return None

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        """Save events to database with deduplication."""
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
            return 0
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()


async def scrape_visitrijeka_events(max_pages: int = 5) -> Dict:
    """Main scraping function for VisitRijeka events."""
    scraper = VisitRijekaScraper()
    try:
        events = await scraper.scrape_all_events(max_pages=max_pages)
        saved = scraper.save_events_to_database(events)
        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved,
            "message": f"Scraped {len(events)} events from VisitRijeka.hr, saved {saved} new events",
        }
    except Exception as e:
        return {"status": "error", "message": f"VisitRijeka scraping failed: {e}"}