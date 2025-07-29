"""
Croatia.hr events scraper for https://croatia.hr/hr-hr/dogadanja
This scraper handles the Vue.js-based dynamic content and extracts event information.
"""

import asyncio
import json
import logging
import os
import re
import time
from datetime import date, datetime
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup, Tag
from sqlalchemy.orm import Session

from ..core.config import settings

# Set up logging
logger = logging.getLogger(__name__)
from ..core.database import SessionLocal
from ..models.event import Event
from ..models.schemas import EventCreate

# BrightData configuration (reuse from entrio scraper)
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

HEADERS = {
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "accept-language": "hr-HR,hr;q=0.9,en;q=0.8",
    "accept-encoding": "gzip, deflate, br",
}

BASE_URL = "https://croatia.hr"
EVENTS_URL = "https://croatia.hr/hr-hr/dogadanja"


class CroatiaEventDataTransformer:
    """Transform scraped Croatia.hr event data to database format."""

    @staticmethod
    def parse_croatian_date(date_str: str) -> Optional[date]:
        """Parse Croatian date formats into Python date object."""
        if not date_str:
            return None

        # Clean the date string
        date_str = date_str.strip()

        # Croatian month names mapping
        croatian_months = {
            "siječnja": 1,
            "siječanj": 1,
            "veljače": 2,
            "veljača": 2,
            "ožujka": 3,
            "ožujak": 3,
            "travnja": 4,
            "travanj": 4,
            "svibnja": 5,
            "svibanj": 5,
            "lipnja": 6,
            "lipanj": 6,
            "srpnja": 7,
            "srpanj": 7,
            "kolovoza": 8,
            "kolovoz": 8,
            "rujna": 9,
            "rujan": 9,
            "listopada": 10,
            "listopad": 10,
            "studenoga": 11,
            "studeni": 11,
            "prosinca": 12,
            "prosinac": 12,
        }

        # Common date patterns for Croatia.hr
        patterns = [
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})",  # DD.MM.YYYY
            r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
            r"(\d{1,2})\.\s*(\w+)\s*(\d{4})",  # DD. Month YYYY
            r"(\d{1,2})\s+(\w+)\s+(\d{4})",  # DD Month YYYY
            r"(\w+)\s+(\d{4})",  # Month YYYY (default to 1st)
        ]

        for pattern in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    if "." in pattern and len(match.groups()) == 3:
                        day, month, year = match.groups()
                        if month.isdigit():
                            return date(int(year), int(month), int(day))
                        else:
                            # Month name
                            month_num = croatian_months.get(month.lower(), 1)
                            return date(int(year), month_num, int(day))
                    elif "-" in pattern:
                        year, month, day = match.groups()
                        return date(int(year), int(month), int(day))
                    elif len(match.groups()) == 2:
                        # Month and year only
                        month_name, year = match.groups()
                        month_num = croatian_months.get(month_name.lower(), 1)
                        return date(int(year), month_num, 1)
                except (ValueError, TypeError):
                    continue

        # Fallback: try to extract year
        year_match = re.search(r"(\d{4})", date_str)
        if year_match:
            try:
                return date(int(year_match.group(1)), 1, 1)
            except ValueError:
                pass

        return None

    @staticmethod
    def parse_time(time_str: str) -> str:
        """Parse time string and return in HH:MM format."""
        if not time_str:
            return "09:00"  # Default time for day events

        # Look for time patterns
        time_match = re.search(r"(\d{1,2}):(\d{2})", time_str)
        if time_match:
            hour, minute = time_match.groups()
            return f"{int(hour):02d}:{minute}"

        # Look for hour only
        hour_match = re.search(r"(\d{1,2})h", time_str)
        if hour_match:
            hour = hour_match.group(1)
            return f"{int(hour):02d}:00"

        return "09:00"  # Default time

    @staticmethod
    def clean_text(text: str) -> str:
        """Clean and normalize text."""
        if not text:
            return ""
        # Remove extra whitespace and normalize
        text = " ".join(text.strip().split())
        # Remove common unwanted characters
        text = re.sub(r"[^\w\s\.,!?-]", "", text, flags=re.UNICODE)
        return text.strip()

    @staticmethod
    def extract_location(location_data: Dict) -> str:
        """Extract and format location from Croatia.hr location data with enhanced address support."""
        parts = []
        
        # Handle enhanced address data from detailed scraping
        if isinstance(location_data, dict):
            # Priority order: street_address > venue > city > region
            if location_data.get("street_address"):
                parts.append(location_data["street_address"])
            elif location_data.get("venue"):
                parts.append(location_data["venue"])
            
            # Add city information
            city = location_data.get("city") or location_data.get("city_name")
            if city:
                parts.append(city)
            elif location_data.get("place"):
                parts.append(location_data["place"])
            
            # Add region/county if available and not already included
            region = location_data.get("county") or location_data.get("region")
            if region and region not in str(parts):
                parts.append(region)
            
            # If we have detected address pattern, prioritize it over basic parts
            if location_data.get("detected_address"):
                return location_data["detected_address"]
            
            # If we have enhanced location data, use it
            if location_data.get("full_location") and not parts:
                return location_data["full_location"]
        
        # Original logic for backward compatibility
        if isinstance(location_data, dict):
            # Try different location fields
            if location_data.get("place") and not any("place" in str(p).lower() for p in parts):
                parts.append(location_data["place"])
            if location_data.get("county") and not any("county" in str(p).lower() for p in parts):
                parts.append(location_data["county"])
            if location_data.get("region") and not any("region" in str(p).lower() for p in parts):
                parts.append(location_data["region"])

        if parts:
            # Clean and deduplicate parts
            unique_parts = []
            for part in parts:
                part_clean = str(part).strip()
                if part_clean and part_clean not in unique_parts:
                    unique_parts.append(part_clean)
            return ", ".join(unique_parts)

        # Fallback to any string in location_data
        if isinstance(location_data, dict):
            for key, value in location_data.items():
                if isinstance(value, str) and value.strip():
                    return value.strip()
        elif isinstance(location_data, str):
            stripped = location_data.strip()
            return stripped if stripped else "Croatia"

        return "Croatia"

    @staticmethod
    def transform_to_event_create(scraped_data: Dict) -> Optional[EventCreate]:
        """Transform scraped Croatia.hr data to EventCreate schema."""
        try:
            # Extract and clean basic fields
            name = CroatiaEventDataTransformer.clean_text(scraped_data.get("title", ""))
            description = CroatiaEventDataTransformer.clean_text(
                scraped_data.get("description", "")
                or scraped_data.get("shortDescription", "")
                or scraped_data.get("intro", "")
            )

            # Handle location
            location_data = scraped_data.get("location", {})
            if isinstance(location_data, str):
                location = location_data
            else:
                location = CroatiaEventDataTransformer.extract_location(location_data)

            # Parse dates
            start_date_str = scraped_data.get("startDate", "") or scraped_data.get(
                "date", ""
            )
            parsed_date = CroatiaEventDataTransformer.parse_croatian_date(
                start_date_str
            )
            if not parsed_date:
                # Skip events without valid dates
                return None

            # Parse time
            time_str = scraped_data.get("time", "") or scraped_data.get("startTime", "")
            parsed_time = CroatiaEventDataTransformer.parse_time(time_str)

            # Handle image URL
            image_url = scraped_data.get("image", "") or scraped_data.get(
                "imageUrl", ""
            )
            if image_url and not image_url.startswith("http"):
                image_url = urljoin(BASE_URL, image_url)

            # Handle event link
            link = (
                scraped_data.get("link", "")
                or scraped_data.get("url", "")
                or scraped_data.get("sefUrl", "")
            )
            if link and not link.startswith("http"):
                link = urljoin(BASE_URL, link)

            # Handle price
            price = scraped_data.get("price", "") or scraped_data.get("ticketPrice", "")
            if not price:
                price = "Free" if scraped_data.get("isFree") else "Check website"

            # Validate required fields
            if not name or len(name) < 3:
                return None

            if not location:
                location = "Croatia"

            if not description:
                description = f"Event in Croatia: {name}"

            return EventCreate(
                name=name,
                time=parsed_time,
                date=parsed_date,
                location=location,
                description=description,
                price=price,
                image=image_url,
                link=link,
            )

        except Exception as e:
            logger.error(f"Error transforming Croatia.hr event data: {e}")
            return None


class CroatiaPlaywrightScraper:
    """Scraper using Playwright for Croatia.hr dynamic content."""

    async def fetch_event_details(self, page, event_url: str) -> Dict:
        """Fetch detailed address information from event page."""
        try:
            await page.goto(event_url, wait_until="domcontentloaded", timeout=30000)
            await page.wait_for_timeout(2000)  # Wait for content to load
            
            # Extract detailed location information
            event_details = await page.evaluate(
                """
                () => {
                    const details = {};
                    
                    // Look for detailed address information
                    const addressSelectors = [
                        '[class*="location"]',
                        '[class*="address"]',
                        '[class*="venue"]',
                        '[class*="adresa"]',
                        '[class*="lokacija"]',
                        '.event-location',
                        '.venue-info',
                        '.location-details'
                    ];
                    
                    for (const selector of addressSelectors) {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            const text = el.textContent.trim();
                            if (text && text.length > 2) {
                                // Extract city name from links
                                const cityLink = el.querySelector('a[href*="visit"]');
                                if (cityLink) {
                                    details.city = cityLink.textContent.trim();
                                    details.city_url = cityLink.href;
                                }
                                
                                // Look for venue or address text
                                const venueSelectors = [
                                    '.venue', '.venue-name', '.location-name',
                                    '[class*="venue"]', '[class*="hall"]',
                                    '.address', '[class*="address"]'
                                ];
                                
                                for (const venueSelector of venueSelectors) {
                                    const venueEl = el.querySelector(venueSelector);
                                    if (venueEl && venueEl.textContent.trim()) {
                                        details.venue = venueEl.textContent.trim();
                                    }
                                }
                                
                                // Store full location text
                                if (!details.full_location || text.length > details.full_location.length) {
                                    details.full_location = text;
                                }
                            }
                        });
                    }
                    
                    // Look for structured address patterns in page content
                    const pageText = document.body.textContent;
                    const addressPatterns = [
                        /([A-ZČĆĐŠŽ][a-zčćđšž\s]+(?:ulica|cesta|trg|put|avenija|bb)\s*\d*[a-z]?)/gi,
                        /(\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)/gi,
                        /([A-ZČĆĐŠŽ][a-zčćđšž\s]+\s+\d+[a-z]?\s*,\s*\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)/gi
                    ];
                    
                    for (const pattern of addressPatterns) {
                        const matches = pageText.match(pattern);
                        if (matches && matches.length > 0) {
                            details.street_address = matches[0].trim();
                            break;
                        }
                    }
                    
                    return details;
                }
                """
            )
            
            return event_details
        
        except Exception as e:
            logger.error(f"Error fetching event details from {event_url}: {e}")
            return {}

    async def scrape_with_playwright(
        self, start_url: str = EVENTS_URL, max_pages: int = 5, fetch_details: bool = False
    ) -> List[Dict]:
        """Scrape events using Playwright to handle Vue.js content."""
        from playwright.async_api import async_playwright

        all_events = []
        page_count = 0

        async with async_playwright() as p:
            if USE_PROXY:
                browser = await p.chromium.connect_over_cdp(BRD_WSS)
            else:
                browser = await p.chromium.launch()

            page = await browser.new_page()

            try:
                logger.info(f"→ Fetching Croatia.hr events from {start_url}")
                await page.goto(start_url, wait_until="domcontentloaded", timeout=90000)

                # Wait for Vue.js to load and render content
                logger.info("Waiting for Vue.js content to load...")
                await page.wait_for_timeout(5000)

                # Try to wait for event containers to appear
                await page.wait_for_selector(
                    '[class*="event"], [class*="card"], [class*="item"], a[href*="/dogadanja/"]',
                    timeout=30000,
                )

                page_count = 0
                while page_count < max_pages:
                    page_count += 1
                    logger.info(f"Scraping page {page_count}...")

                    # Wait a bit more for dynamic content
                    await page.wait_for_timeout(3000)

                    # Extract events using JavaScript evaluation
                    events_data = await page.evaluate(
                        """
                        () => {
                            const events = [];
                            
                            // Multiple selector strategies for Croatia.hr
                            const eventSelectors = [
                                'a[href*="/dogadanja/"]',
                                '[class*="event"]',
                                '[class*="card"]',
                                '[class*="item"]',
                                '.mosaic-item',
                                '.card-item',
                                'article',
                                '[data-module*="event"]'
                            ];
                            
                            let eventElements = [];
                            
                            // Try each selector until we find events
                            for (const selector of eventSelectors) {
                                const elements = document.querySelectorAll(selector);
                                if (elements.length > 0) {
                                    // Filter for actual event links
                                    eventElements = Array.from(elements).filter(el => {
                                        const href = el.href || el.querySelector('a')?.href;
                                        return href && (href.includes('/dogadanja/') || href.includes('/events/'));
                                    });
                                    if (eventElements.length > 0) break;
                                }
                            }
                            
                            eventElements.forEach((element, index) => {
                                try {
                                    const data = {};
                                    
                                    // Extract link
                                    const linkEl = element.href ? element : element.querySelector('a');
                                    if (linkEl && linkEl.href) {
                                        data.link = linkEl.href;
                                    }
                                    
                                    // Extract title from multiple possible locations
                                    const titleSelectors = [
                                        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                                        '.title', '.name', '.event-title',
                                        '[class*="title"]', '[class*="name"]',
                                        '.card-title', '.item-title'
                                    ];
                                    
                                    for (const selector of titleSelectors) {
                                        const titleEl = element.querySelector(selector);
                                        if (titleEl && titleEl.textContent.trim()) {
                                            data.title = titleEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    // If no title found, try link text or alt text
                                    if (!data.title && linkEl) {
                                        data.title = linkEl.textContent.trim() || linkEl.getAttribute('title') || linkEl.getAttribute('alt');
                                    }
                                    
                                    // Extract date
                                    const dateSelectors = [
                                        '.date', '.event-date', '.start-date',
                                        '[class*="date"]', 'time', '.time',
                                        '.when', '.datum'
                                    ];
                                    
                                    for (const selector of dateSelectors) {
                                        const dateEl = element.querySelector(selector);
                                        if (dateEl && dateEl.textContent.trim()) {
                                            data.date = dateEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    // Extract location with enhanced address detection
                                    const locationSelectors = [
                                        '.location', '.place', '.venue', '.where',
                                        '[class*="location"]', '[class*="place"]',
                                        '[class*="venue"]', '[class*="address"]',
                                        '[class*="adresa"]', '[class*="lokacija"]',
                                        '.city', '.region', '.mjesto', '.grad'
                                    ];
                                    
                                    for (const selector of locationSelectors) {
                                        const locationEl = element.querySelector(selector);
                                        if (locationEl && locationEl.textContent.trim()) {
                                            data.location = locationEl.textContent.trim();
                                            
                                            // Try to extract more detailed address info from the element
                                            const linkEl = locationEl.querySelector('a');
                                            if (linkEl) {
                                                data.city_link = linkEl.href;
                                                data.city_name = linkEl.textContent.trim();
                                            }
                                            
                                            // Look for venue/address within the location element
                                            const venueSelectors = [
                                                '.venue', '.venue-name', '[class*="venue"]',
                                                '.address', '[class*="address"]',
                                                '.street', '[class*="street"]'
                                            ];
                                            
                                            for (const venueSelector of venueSelectors) {
                                                const venueEl = locationEl.querySelector(venueSelector);
                                                if (venueEl && venueEl.textContent.trim()) {
                                                    data.venue = venueEl.textContent.trim();
                                                    break;
                                                }
                                            }
                                            break;
                                        }
                                    }
                                    
                                    // Additional address pattern detection in text content
                                    const fullText = element.textContent;
                                    if (fullText) {
                                        // Look for Croatian address patterns
                                        const addressPatterns = [
                                            /\b[\w\s]+\s+\d+[a-z]?\s*,\s*\d{5}\s+[\w\s]+/gi,  // Street Number, Postal City
                                            /\b[\w\s]+\s+(ulica|cesta|trg|put|avenija)\s*\d*[a-z]?\b/gi,  // Croatian street types
                                            /\b\d{5}\s+[\w\s]+\b/gi  // Postal code + city
                                        ];
                                        
                                        for (const pattern of addressPatterns) {
                                            const matches = fullText.match(pattern);
                                            if (matches && matches.length > 0) {
                                                data.detected_address = matches[0].trim();
                                                break;
                                            }
                                        }
                                    }
                                    
                                    // Extract description
                                    const descSelectors = [
                                        '.description', '.summary', '.excerpt',
                                        '.intro', '.content', 'p',
                                        '[class*="description"]', '[class*="summary"]'
                                    ];
                                    
                                    for (const selector of descSelectors) {
                                        const descEl = element.querySelector(selector);
                                        if (descEl && descEl.textContent.trim().length > 20) {
                                            data.description = descEl.textContent.trim();
                                            break;
                                        }
                                    }
                                    
                                    // Extract image
                                    const imgEl = element.querySelector('img');
                                    if (imgEl) {
                                        data.image = imgEl.src || imgEl.getAttribute('data-src') || imgEl.getAttribute('data-lazy');
                                    }
                                    
                                    // Extract additional data from data attributes or Vue.js data
                                    const dataAttrs = element.getAttributeNames().filter(name => name.startsWith('data-'));
                                    dataAttrs.forEach(attr => {
                                        const value = element.getAttribute(attr);
                                        if (value && value.length < 500) {
                                            data[attr.replace('data-', '')] = value;
                                        }
                                    });
                                    
                                    // Only add if we have meaningful data
                                    if (data.title || data.link) {
                                        events.push(data);
                                    }
                                } catch (error) {
                                    console.error(`Error processing event ${index}:`, error);
                                }
                            });
                            
                            return events;
                        }
                    """
                    )

                    valid_events = [
                        event
                        for event in events_data
                        if event.get("title") or event.get("link")
                    ]
                    
                    # Fetch detailed address information if requested
                    if fetch_details and valid_events:
                        logger.info(f"Fetching detailed address info for {len(valid_events)} events...")
                        enhanced_events = []
                        
                        for i, event in enumerate(valid_events):
                            if event.get("link"):
                                try:
                                    # Rate limiting - fetch details for every 3rd event to avoid overwhelming the server
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

                    logger.info(
                        f"Page {page_count}: Found {len(valid_events)} events (Total: {len(all_events)})"
                    )

                    # Try to find pagination or load more button
                    has_more = False

                    # Look for "Load More" or pagination buttons
                    load_more_selectors = [
                        'button[class*="load-more"]',
                        'button[class*="next"]',
                        'a[class*="next"]',
                        ".pagination a:last-child",
                        'button:contains("Učitaj više")',
                        'button:contains("Više")',
                        'a:contains("Sljedeća")',
                    ]

                    for selector in load_more_selectors:
                        try:
                            load_more = await page.query_selector(selector)
                            if load_more:
                                is_enabled = await load_more.is_enabled()
                                if is_enabled:
                                    logger.info(f"Found load more button: {selector}")
                                    await load_more.click()
                                    await page.wait_for_timeout(
                                        3000
                                    )  # Wait for new content
                                    has_more = True
                                    break
                        except Exception as e:
                            logger.error(f"Error clicking load more button: {e}")
                            continue

                    # If no "load more" found, try scrolling to trigger infinite scroll
                    if not has_more:
                        try:
                            previous_events_count = len(all_events)
                            await page.evaluate(
                                "window.scrollTo(0, document.body.scrollHeight)"
                            )
                            await page.wait_for_timeout(3000)

                            # Check if new events appeared
                            new_events_data = await page.evaluate(
                                'document.querySelectorAll(\'a[href*="/dogadanja/"], [class*="event"]\').length'
                            )
                            if new_events_data > previous_events_count:
                                has_more = True
                                logger.info("Infinite scroll detected more content")

                        except Exception as e:
                            logger.error(f"Error with infinite scroll: {e}")

                    if not has_more or len(valid_events) == 0:
                        logger.info("No more pages found or no events on current page")
                        break

            except Exception as e:
                logger.error(f"Error during scraping: {e}")

            finally:
                await browser.close()

        return all_events


class CroatiaScraper:
    """Main scraper class for Croatia.hr events."""

    def __init__(self):
        self.playwright_scraper = CroatiaPlaywrightScraper()
        self.transformer = CroatiaEventDataTransformer()

    async def scrape_events(self, max_pages: int = 5, fetch_details: bool = False) -> List[EventCreate]:
        """Scrape events and return as EventCreate objects."""
        logger.info(f"Starting Croatia.hr scraper (max_pages: {max_pages}, fetch_details: {fetch_details})")

        # Scrape raw data using Playwright (required for Vue.js content)
        raw_events = await self.playwright_scraper.scrape_with_playwright(
            max_pages=max_pages, fetch_details=fetch_details
        )

        logger.info(f"Scraped {len(raw_events)} raw events from Croatia.hr")

        # Transform to EventCreate objects
        events = []
        for raw_event in raw_events:
            event = self.transformer.transform_to_event_create(raw_event)
            if event:
                events.append(event)

        logger.info(f"Transformed {len(events)} valid events for Croatia.hr")
        return events

    def save_events_to_database(self, events: List[EventCreate]) -> int:
        """Save events to database and return count of saved events."""
        if not events:
            return 0

        db = SessionLocal()
        saved_count = 0

        try:
            for event_data in events:
                # Check if event already exists (by name and date)
                existing = (
                    db.query(Event)
                    .filter(
                        Event.title == event_data.title, Event.date == event_data.date
                    )
                    .first()
                )

                if not existing:
                    db_event = Event(**event_data.model_dump())
                    db.add(db_event)
                    saved_count += 1
                else:
                    logger.info(f"Event already exists: {event_data.title}")

            db.commit()
            logger.info(f"Saved {saved_count} new events to database from Croatia.hr")

        except Exception as e:
            logger.error(f"Error saving Croatia.hr events to database: {e}")
            db.rollback()
            raise
        finally:
            db.close()

        return saved_count


# Convenience function for API endpoints
async def scrape_croatia_events(max_pages: int = 5, fetch_details: bool = False) -> Dict:
    """Scrape Croatia.hr events and save to database."""
    scraper = CroatiaScraper()

    try:
        events = await scraper.scrape_events(max_pages=max_pages, fetch_details=fetch_details)
        saved_count = scraper.save_events_to_database(events)

        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved_count,
            "message": f"Successfully scraped {len(events)} events from Croatia.hr, saved {saved_count} new events",
        }

    except Exception as e:
        return {"status": "error", "message": f"Croatia.hr scraping failed: {str(e)}"}
