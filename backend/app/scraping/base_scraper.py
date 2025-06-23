"""Base scraper class with common functionality for all Croatian event scrapers."""

from __future__ import annotations

import asyncio
import logging
import os
import re
from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from ..models.schemas import EventCreate

# Configure logging
logger = logging.getLogger(__name__)

# BrightData configuration (shared across all scrapers)
BRIGHTDATA_USER = os.getenv("BRIGHTDATA_USER", "demo_user")
BRIGHTDATA_PASSWORD = os.getenv("BRIGHTDATA_PASSWORD", "demo_password")
BRIGHTDATA_HOST_RES = "brd.superproxy.io"
BRIGHTDATA_PORT = int(os.getenv("BRIGHTDATA_PORT", 22225))
SCRAPING_BROWSER_EP = f"https://{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"
PROXY = f"http://{BRIGHTDATA_USER}:{BRIGHTDATA_PASSWORD}@{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"

USE_SCRAPING_BROWSER = os.getenv("USE_SCRAPING_BROWSER", "0") == "1"
USE_PROXY = os.getenv("USE_PROXY", "1") == "1"

DEFAULT_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 ScraperBot/1.0",
}

# Common Croatian month translations
CROATIAN_MONTHS = {
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
    # Croatian names
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


class BaseScraper(ABC):
    """Abstract base class for Croatian event scrapers with common functionality."""

    def __init__(
        self,
        base_url: str,
        events_url: str,
        source_name: str,
        headers: Optional[Dict[str, str]] = None,
        use_proxy: Optional[bool] = None,
        use_scraping_browser: Optional[bool] = None,
    ):
        """Initialize base scraper.
        
        Args:
            base_url: Base URL for the website
            events_url: URL for events listing page
            source_name: Name to use as source in EventCreate
            headers: Custom headers (defaults to DEFAULT_HEADERS)
            use_proxy: Override proxy usage
            use_scraping_browser: Override scraping browser usage
        """
        self.base_url = base_url
        self.events_url = events_url
        self.source_name = source_name
        self.headers = headers or DEFAULT_HEADERS.copy()
        self.use_proxy = use_proxy if use_proxy is not None else USE_PROXY
        self.use_scraping_browser = use_scraping_browser if use_scraping_browser is not None else USE_SCRAPING_BROWSER
        
        # HTTP client will be initialized in setup_client()
        self.client: Optional[httpx.AsyncClient] = None
        
        logger.info(f"Initialized {self.__class__.__name__} for {source_name}")

    async def setup_client(self) -> None:
        """Setup HTTP client with appropriate configuration."""
        if self.client:
            return
            
        if self.use_proxy and not self.use_scraping_browser:
            self.client = httpx.AsyncClient(
                headers=self.headers,
                proxies={"http": PROXY, "https": PROXY},
                verify=False,
                timeout=30.0,
            )
            logger.info("HTTP client configured with proxy")
        else:
            self.client = httpx.AsyncClient(
                headers=self.headers,
                timeout=30.0,
            )
            logger.info("HTTP client configured without proxy")

    async def fetch_with_retry(
        self, 
        url: str, 
        max_retries: int = 3, 
        backoff_factor: float = 1.0
    ) -> httpx.Response:
        """Fetch URL with retry logic and exponential backoff.
        
        Args:
            url: URL to fetch
            max_retries: Maximum number of retry attempts
            backoff_factor: Base delay for exponential backoff
            
        Returns:
            HTTP response
            
        Raises:
            RuntimeError: If all retry attempts fail
        """
        await self.setup_client()
        
        for attempt in range(max_retries + 1):
            try:
                if self.use_scraping_browser and self.use_proxy:
                    params = {"url": url}
                    response = await self.client.get(
                        SCRAPING_BROWSER_EP,
                        params=params,
                        auth=(BRIGHTDATA_USER, BRIGHTDATA_PASSWORD),
                    )
                else:
                    response = await self.client.get(url)
                    
                response.raise_for_status()
                logger.debug(f"Successfully fetched {url} on attempt {attempt + 1}")
                return response
                
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                if attempt == max_retries:
                    logger.error(f"Failed to fetch {url} after {max_retries + 1} attempts: {e}")
                    raise RuntimeError(f"Request failed for {url} after {max_retries + 1} attempts: {e}")
                
                delay = backoff_factor * (2 ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}. Retrying in {delay}s...")
                await asyncio.sleep(delay)

    @staticmethod
    def parse_date(date_str: str) -> Optional[date]:
        """Parse various Croatian and international date formats.
        
        Args:
            date_str: Raw date string
            
        Returns:
            Parsed date or None if parsing fails
        """
        if not date_str:
            return None
            
        date_str = date_str.strip()
        
        # Common date patterns
        patterns = [
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})",     # DD.MM.YYYY
            r"(\d{4})-(\d{1,2})-(\d{1,2})",       # YYYY-MM-DD
            r"(\d{1,2})\s+(\w+)\s*(\d{4})",       # DD Month YYYY
            r"(\d{1,2})\.(\d{1,2})\.",            # DD.MM. (current year)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if pattern == r"(\d{1,2})\.(\d{1,2})\.(\d{4})":
                        day, month, year = match.groups()
                        return date(int(year), int(month), int(day))
                    elif pattern == r"(\d{4})-(\d{1,2})-(\d{1,2})":
                        year, month, day = match.groups()
                        return date(int(year), int(month), int(day))
                    elif pattern == r"(\d{1,2})\s+(\w+)\s*(\d{4})":
                        day, month_name, year = match.groups()
                        month_num = CROATIAN_MONTHS.get(month_name.lower())
                        if month_num:
                            return date(int(year), month_num, int(day))
                    elif pattern == r"(\d{1,2})\.(\d{1,2})\.":
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
        
        # Fallback: try to extract year and assume January 1st
        year_match = re.search(r"(\d{4})", date_str)
        if year_match:
            try:
                return date(int(year_match.group(1)), 1, 1)
            except ValueError:
                pass
                
        logger.warning(f"Could not parse date: {date_str}")
        return None

    @staticmethod
    def parse_time(time_str: str) -> str:
        """Parse time string and return in HH:MM format.
        
        Args:
            time_str: Raw time string
            
        Returns:
            Time in HH:MM format, defaults to "20:00"
        """
        if not time_str:
            return "20:00"
            
        # Match HH:MM format
        match = re.search(r"(\d{1,2}):(\d{2})", time_str)
        if match:
            hour, minute = match.groups()
            return f"{int(hour):02d}:{minute}"
            
        # Match HH h format (Croatian)
        match = re.search(r"(\d{1,2})h", time_str)
        if match:
            hour = match.group(1)
            return f"{int(hour):02d}:00"
            
        logger.debug(f"Could not parse time: {time_str}, using default 20:00")
        return "20:00"

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text content.
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text with normalized whitespace
        """
        return " ".join(text.split()) if text else ""

    def make_absolute_url(self, url: str) -> str:
        """Convert relative URL to absolute using base_url.
        
        Args:
            url: Relative or absolute URL
            
        Returns:
            Absolute URL
        """
        if not url:
            return url
        if url.startswith("http"):
            return url
        return urljoin(self.base_url, url)

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        if self.client:
            await self.client.aclose()
            self.client = None
            logger.debug(f"Closed HTTP client for {self.__class__.__name__}")

    @abstractmethod
    async def parse_event_detail(self, url: str) -> Dict[str, Any]:
        """Parse detailed event information from event page.
        
        Args:
            url: Event detail page URL
            
        Returns:
            Dictionary with event details
        """
        pass

    @abstractmethod
    def parse_listing_element(self, element: Tag) -> Dict[str, Any]:
        """Parse event information from listing page element.
        
        Args:
            element: BeautifulSoup element containing event info
            
        Returns:
            Dictionary with basic event details
        """
        pass

    @abstractmethod
    def transform_to_event(self, raw_data: Dict[str, Any]) -> Optional[EventCreate]:
        """Transform raw scraped data to EventCreate object.
        
        Args:
            raw_data: Raw event data dictionary
            
        Returns:
            EventCreate object or None if transformation fails
        """
        pass

    async def scrape_events_page(self, url: str) -> tuple[List[Dict[str, Any]], Optional[str]]:
        """Scrape events from a single page.
        
        Args:
            url: Page URL to scrape
            
        Returns:
            Tuple of (events list, next page URL)
        """
        logger.info(f"Scraping events page: {url}")
        
        try:
            response = await self.fetch_with_retry(url)
            soup = BeautifulSoup(response.text, "html.parser")
            
            events = []
            containers = self._find_event_containers(soup)
            
            logger.info(f"Found {len(containers)} event containers")
            
            # Parse listing elements and gather detail URLs
            listing_data = []
            detail_urls = []
            
            for container in containers:
                if isinstance(container, Tag):
                    data = self.parse_listing_element(container)
                    if data:
                        listing_data.append(data)
                        if data.get("link"):
                            detail_urls.append(data["link"])
            
            # Fetch details concurrently if we have URLs
            if detail_urls:
                logger.info(f"Fetching details for {len(detail_urls)} events")
                detail_tasks = [
                    self.parse_event_detail(url) for url in detail_urls
                ]
                details = await asyncio.gather(*detail_tasks, return_exceptions=True)
                
                # Merge listing and detail data
                for listing, detail in zip(listing_data, details):
                    if isinstance(detail, dict):
                        # Update listing with detail data, preserving listing values
                        merged = {**detail, **{k: v for k, v in listing.items() if v}}
                        events.append(merged)
                    else:
                        # Detail fetch failed, use listing data
                        if isinstance(detail, Exception):
                            logger.warning(f"Failed to fetch details for {listing.get('link')}: {detail}")
                        events.append(listing)
            else:
                events = listing_data
            
            # Find next page URL
            next_url = self._find_next_page_url(soup, url)
            
            return events, next_url
            
        except Exception as e:
            logger.error(f"Failed to scrape events page {url}: {e}")
            raise

    @abstractmethod
    def _find_event_containers(self, soup: BeautifulSoup) -> List[Tag]:
        """Find event container elements on the page.
        
        Args:
            soup: BeautifulSoup parsed page
            
        Returns:
            List of event container elements
        """
        pass

    def _find_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """Find next page URL from pagination.
        
        Args:
            soup: BeautifulSoup parsed page
            current_url: Current page URL
            
        Returns:
            Next page URL or None
        """
        selectors = [
            'a[rel="next"]',
            '.pagination-next a',
            'a.next',
            'a.load-more',
            'button.load-more'
        ]
        
        for selector in selectors:
            next_link = soup.select_one(selector)
            if next_link and next_link.get("href"):
                next_url = self.make_absolute_url(next_link.get("href"))
                logger.debug(f"Found next page URL: {next_url}")
                return next_url
        
        return None

    async def scrape_all_events(self, max_pages: int = 10) -> List[EventCreate]:
        """Scrape events from all pages up to max_pages.
        
        Args:
            max_pages: Maximum number of pages to scrape
            
        Returns:
            List of EventCreate objects
        """
        logger.info(f"Starting scraping for {self.source_name}, max pages: {max_pages}")
        
        all_events = []
        current_url = self.events_url
        page = 0
        
        try:
            while current_url and page < max_pages:
                page += 1
                logger.info(f"Scraping page {page}: {current_url}")
                
                raw_events, next_url = await self.scrape_events_page(current_url)
                
                # Transform raw events to EventCreate objects
                for raw_event in raw_events:
                    event = self.transform_to_event(raw_event)
                    if event:
                        all_events.append(event)
                
                logger.info(f"Page {page}: Found {len(raw_events)} raw events, {len([e for e in raw_events if self.transform_to_event(e)])} valid events")
                
                if not next_url or not raw_events:
                    logger.info("No more pages or events found, stopping")
                    break
                    
                current_url = next_url
                
                # Be nice to the server
                await asyncio.sleep(1)
                
        finally:
            await self.close()
        
        logger.info(f"Scraping completed for {self.source_name}: {len(all_events)} total events")
        return all_events