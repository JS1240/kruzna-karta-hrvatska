"""
Croatia.hr events scraper for https://croatia.hr/hr-hr/dogadanja
This scraper handles the Vue.js-based dynamic content and extracts event information.
"""

import logging
import re
from datetime import date, datetime
from typing import Dict, List, Optional
from urllib.parse import urljoin

from app.config.components import get_settings
from app.core.database import SessionLocal
from app.core.geocoding_service import geocoding_service
from app.models.event import Event
from app.models.schemas import EventCreate

# Set up logging
logger = logging.getLogger(__name__)

# Load configuration
CONFIG = get_settings()

# BrightData configuration from centralized settings
SCRAPING_CONFIG = CONFIG.scraping
USER = SCRAPING_CONFIG.brightdata_user
PASSWORD = SCRAPING_CONFIG.brightdata_password
BRIGHTDATA_HOST_RES = SCRAPING_CONFIG.brightdata_host
BRIGHTDATA_PORT = SCRAPING_CONFIG.brightdata_port

# WebSocket URL for Bright Data scraping browser
BRD_WSS = SCRAPING_CONFIG.scraping_browser_endpoint if SCRAPING_CONFIG.is_websocket_endpoint else f"wss://{USER}:{PASSWORD}@{BRIGHTDATA_HOST_RES}:9222"

# Proxy URL
PROXY = f"http://{USER}:{PASSWORD}@{BRIGHTDATA_HOST_RES}:{BRIGHTDATA_PORT}"

# Configuration flags
USE_PROXY = SCRAPING_CONFIG.use_proxy
USE_PLAYWRIGHT = SCRAPING_CONFIG.use_playwright
USE_SB = bool(SCRAPING_CONFIG.scraping_browser_url)

# Headers from configuration
HEADERS = SCRAPING_CONFIG.headers_dict

EVENTS_URL = "https://croatia.hr/hr-hr/dogadanja"


class CroatiaEventDataTransformer:
    """Transform scraped Croatia.hr event data to database format."""

    # Event category mapping based on Croatian keywords and content analysis
    EVENT_CATEGORIES = {
        "music": {
            "keywords": ["koncert", "glazba", "muzika", "festival", "opera", "jazz", "rock", "pop", "klasična", "folklor", "pjevanje", "bend", "orkestra"],
            "category": "Music"
        },
        "culture": {
            "keywords": ["kultura", "kazalište", "teatar", "predstava", "izložba", "galerija", "muzej", "umjetnost", "balet", "ples", "tradicija", "baština"],
            "category": "Culture"
        },
        "sports": {
            "keywords": ["sport", "nogomet", "košarka", "tenis", "atletika", "biciklizam", "trčanje", "maraton", "turnir", "utakmica", "prvenstvo", "natjecanje"],
            "category": "Sports"
        },
        "food": {
            "keywords": ["gastro", "hrana", "vino", "degustacija", "kulinarski", "restoran", "festival hrane", "kuhanje", "jelo", "specijaliteti", "lokalna kuhinja"],
            "category": "Food & Drink"
        },
        "festival": {
            "keywords": ["festival", "manifestacija", "smotra", "sajam", "karnaval", "proslave", "tradicionalni", "godišnji", "ljetni", "zimski"],
            "category": "Festival"
        },
        "education": {
            "keywords": ["edukacija", "radionica", "seminar", "predavanje", "tečaj", "učenje", "znanje", "obrazovanje", "škola", "fakultet"],
            "category": "Education"
        },
        "family": {
            "keywords": ["djeca", "obitelj", "animacija", "igra", "zabava", "radionica za djecu", "porodica", "djeca i roditelji", "mala djeca"],
            "category": "Family"
        },
        "nightlife": {
            "keywords": ["noćni život", "klub", "zabava", "party", "diskoteka", "cocktail", "bar", "noćni", "after party"],
            "category": "Nightlife"
        },
        "nature": {
            "keywords": ["priroda", "park", "planina", "more", "rijeka", "jezero", "šuma", "staza", "izlet", "aktivnost na otvorenom", "avantura"],
            "category": "Nature & Outdoor"
        },
        "tourism": {
            "keywords": ["turizam", "obilazak", "razgledavanje", "vođene ture", "destinacija", "spomenik", "kulturno nasljeđe", "lokacije"],
            "category": "Tourism"
        }
    }

    @staticmethod
    def categorize_event(title: str, description: str, location: str = "") -> str:
        """Categorize event based on content analysis using Croatian keywords."""
        content = f"{title} {description} {location}".lower()
        
        # Score each category based on keyword matches
        category_scores = {}
        for cat_key, cat_data in CroatiaEventDataTransformer.EVENT_CATEGORIES.items():
            score = 0
            for keyword in cat_data["keywords"]:
                if keyword in content:
                    # Weight title matches higher
                    if keyword in title.lower():
                        score += 3
                    elif keyword in description.lower():
                        score += 2
                    else:
                        score += 1
            
            if score > 0:
                category_scores[cat_data["category"]] = score
        
        # Return highest scoring category or default
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return "General"

    @staticmethod
    def detect_multiple_events(description: str, title: str) -> List[Dict[str, str]]:
        """Detect multiple events within a single event description."""
        if not description or len(description) < 100:
            return []
        
        multiple_events = []
        
        # Croatian patterns that indicate multiple events
        multi_event_patterns = [
            r"(\d{1,2}\.\s*\d{1,2}\.\s*\d{4}\.?\s*[-–]\s*[^,\n]+)",  # Date - Event pattern
            r"(\d{1,2}\.\s*\d{1,2}\.\s*[-–]\s*[^,\n]+)",  # DD.MM - Event pattern
            r"(\d{1,2}:\d{2}\s*[-–]\s*[^,\n]+)",  # Time - Event pattern
            r"(dan\s+\d+[:.]?\s*[^,\n]+)",  # "dan 1:", "dan 2:" pattern
            r"(\d+\.\s*dan[:.]?\s*[^,\n]+)",  # "1. dan:", "2. dan:" pattern
        ]
        
        # Look for structured event listings
        for pattern in multi_event_patterns:
            matches = re.findall(pattern, description, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                if len(match.strip()) > 20:  # Minimum meaningful length
                    # Extract potential date/time
                    date_match = re.search(r"(\d{1,2}\.\s*\d{1,2}\.?\s*(?:\d{4})?)", match)
                    time_match = re.search(r"(\d{1,2}:\d{2})", match)
                    
                    event_info = {
                        "sub_title": match.strip(),
                        "sub_date": date_match.group(1) if date_match else "",
                        "sub_time": time_match.group(1) if time_match else "",
                        "is_sub_event": True
                    }
                    multiple_events.append(event_info)
        
        # Also check for bullet points or numbered lists
        bullet_patterns = [
            r"^[-•*]\s*(.+)$",  # Bullet points
            r"^\d+\.\s*(.+)$",  # Numbered lists
            r"^[•▪▫]\s*(.+)$",  # Unicode bullets
        ]
        
        lines = description.split('\n')
        for line in lines:
            line = line.strip()
            for pattern in bullet_patterns:
                match = re.match(pattern, line)
                if match and len(match.group(1)) > 15:
                    event_text = match.group(1).strip()
                    # Check if it looks like an event (contains date or time keywords)
                    if any(keyword in event_text.lower() for keyword in ['sat', 'h', ':', 'dan', 'datum', 'vrijeme']):
                        multiple_events.append({
                            "sub_title": event_text,
                            "sub_date": "",
                            "sub_time": "",
                            "is_sub_event": True
                        })
        
        return multiple_events[:5]  # Limit to 5 sub-events to avoid spam

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

        # Enhanced date patterns for Croatia.hr specific formats
        patterns = [
            r"(\d{1,2})\.(\d{1,2})\.(\d{4})",  # DD.MM.YYYY
            r"(\d{4})-(\d{1,2})-(\d{1,2})",  # YYYY-MM-DD
            r"(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})\.",  # DD. MM. YYYY.
            r"(\d{1,2})\.\s*(\w+)\s*(\d{4})",  # DD. Month YYYY
            r"(\d{1,2})\s+(\w+)\s+(\d{4})",  # DD Month YYYY
            r"(\w+)\s+(\d{4})",  # Month YYYY (default to 1st)
            r"(\d{1,2})\.\s*(\d{1,2})\.\s*do\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})",  # DD.MM. do DD.MM.YYYY
            r"od\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})",  # od DD.MM.YYYY
            r"(\d{1,2})\.\s*(\d{1,2})\.\s*-\s*(\d{1,2})\.\s*(\d{1,2})\.\s*(\d{4})",  # DD.MM. - DD.MM.YYYY
            r"(\d{1,2})\.\s*(\d{1,2})\.",  # DD.MM. (current year)
            r"(\d{1,2})\.\s*(\d{1,2})\.\s*do\s*(\d{1,2})\.\s*(\d{1,2})\.",  # DD.MM. do DD.MM. (current year)
        ]

        for pattern in patterns:
            match = re.search(pattern, date_str, re.IGNORECASE)
            if match:
                try:
                    groups = match.groups()
                    
                    # Handle different pattern types
                    if "do" in pattern and len(groups) >= 5:
                        # Date range pattern (DD.MM. do DD.MM.YYYY or similar)
                        if len(groups) == 5:  # DD.MM. do DD.MM.YYYY
                            day, month, _, _, year = groups
                            return date(int(year), int(month), int(day))
                        elif len(groups) == 4:  # DD.MM. do DD.MM. (current year)
                            day, month, _, _ = groups
                            current_year = date.today().year
                            parsed_date = date(current_year, int(month), int(day))
                            if parsed_date < date.today():
                                parsed_date = date(current_year + 1, int(month), int(day))
                            return parsed_date
                    elif "-" in pattern and len(groups) >= 5:
                        # Range with dash (DD.MM. - DD.MM.YYYY)
                        day, month, _, _, year = groups
                        return date(int(year), int(month), int(day))
                    elif "od" in pattern and len(groups) == 3:
                        # "od DD.MM.YYYY" pattern
                        day, month, year = groups
                        return date(int(year), int(month), int(day))
                    elif len(groups) == 3:
                        # Standard DD.MM.YYYY or DD. Month YYYY
                        day, month, year = groups
                        if month.isdigit():
                            return date(int(year), int(month), int(day))
                        else:
                            # Month name
                            month_num = croatian_months.get(month.lower(), 1)
                            return date(int(year), month_num, int(day))
                    elif "-" in pattern and len(groups) == 3:
                        # YYYY-MM-DD
                        year, month, day = groups
                        return date(int(year), int(month), int(day))
                    elif len(groups) == 2:
                        # Month and year only or DD.MM. (current year)
                        if groups[1].isdigit() and len(groups[1]) == 4:
                            # Month YYYY
                            month_name, year = groups
                            month_num = croatian_months.get(month_name.lower(), 1)
                            return date(int(year), month_num, 1)
                        else:
                            # DD.MM. (current year)
                            day, month = groups
                            current_year = date.today().year
                            parsed_date = date(current_year, int(month), int(day))
                            if parsed_date < date.today():
                                parsed_date = date(current_year + 1, int(month), int(day))
                            return parsed_date
                            
                except (ValueError, TypeError) as e:
                    logger.debug(f"Date parsing failed for pattern {pattern} with groups {match.groups()}: {e}")
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
    def parse_croatian_address(text: str) -> Dict[str, str]:
        """Parse Croatian address components from text."""
        if not text:
            return {}
        
        result = {}
        
        # Croatian address patterns
        patterns = {
            "full_address": r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+(?:ulica|cesta|trg|put|avenija|bb)\s*\d*[a-z]?\s*,\s*\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)",
            "street_with_number": r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+(?:ulica|cesta|trg|put|avenija)\s*\d+[a-z]?)",
            "postal_city": r"(\d{5}\s+[A-ZČĆĐŠŽ][a-zčćđšž\s]+)",
            "venue_name": r"([A-ZČĆĐŠŽ][a-zčćđšž\s]+(dvorana|centar|kazalište|kino|klub|restoran|hotel|park))",
            "city_name": r"\b([A-ZČĆĐŠŽ][a-zčćđšž\s]{2,})\b",
        }
        
        for key, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                if key == "full_address":
                    result["full_address"] = matches[0].strip()
                elif key == "street_with_number":
                    result["street"] = matches[0].strip()  
                elif key == "postal_city":
                    postal_city = matches[0].strip()
                    parts = postal_city.split(None, 1)
                    if len(parts) == 2:
                        result["postal_code"] = parts[0]
                        result["city"] = parts[1]
                elif key == "venue_name":
                    result["venue"] = matches[0].strip()
                elif key == "city_name" and "city" not in result:
                    # Take the longest match as most likely city name
                    result["city"] = max(matches, key=len).strip()
        
        return result

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
                # For events without valid dates, use a default future date
                from datetime import date, timedelta
                parsed_date = date.today() + timedelta(days=30)  # Default to 30 days from now
                logger.warning(f"No valid date found for event '{name}', using default: {parsed_date}")

            # Parse time
            time_str = scraped_data.get("time", "") or scraped_data.get("startTime", "")
            parsed_time = CroatiaEventDataTransformer.parse_time(time_str)

            # Handle image URL
            image_url = scraped_data.get("image", "") or scraped_data.get(
                "imageUrl", ""
            )
            if image_url and not image_url.startswith("http"):
                # Extract base URL dynamically from EVENTS_URL
                base_url = "https://croatia.hr"
                image_url = urljoin(base_url, image_url)

            # Handle event link
            link = (
                scraped_data.get("link", "")
                or scraped_data.get("url", "")
                or scraped_data.get("sefUrl", "")
            )
            if link and not link.startswith("http"):
                # Extract base URL dynamically from EVENTS_URL
                base_url = "https://croatia.hr"
                link = urljoin(base_url, link)

            # Handle price
            price = scraped_data.get("price", "") or scraped_data.get("ticketPrice", "")
            if not price:
                price = "Free" if scraped_data.get("isFree") else "Check website"

            # Validate required fields
            if not name or len(name) < 3:
                return None

            if not location or location.strip().lower() in ["croatia", "", "hr"]:
                # Extract location from the URL domain as fallback
                if scraped_data.get("link"):
                    import re
                    # Try to extract city/region from URL patterns
                    url_match = re.search(r"visit([^.]+)\.croatia\.hr", scraped_data["link"])
                    if url_match:
                        city_from_url = url_match.group(1).replace("-", " ").title()
                        # Clean up common URL patterns
                        city_from_url = city_from_url.replace("Central ", "Central-")  # "Central Istria"
                        city_from_url = city_from_url.replace("Dugo Selo", "Dugo Selo")  # Keep proper names
                        location = city_from_url
                    else:
                        # Try other URL patterns
                        domain_match = re.search(r"//([^/]+)\.croatia\.hr", scraped_data["link"])
                        if domain_match:
                            domain_part = domain_match.group(1)
                            if domain_part != "www" and domain_part != "croatia":
                                location = domain_part.replace("-", " ").title()
                            else:
                                location = "Croatia"
                        else:
                            location = "Croatia"
                else:
                    location = "Croatia"

            if not description:
                description = f"Event in Croatia: {name}"

            # Categorize event based on content analysis
            category = CroatiaEventDataTransformer.categorize_event(name, description, location)
            
            # Detect multiple events within description
            multiple_events = CroatiaEventDataTransformer.detect_multiple_events(description, name)
            if multiple_events:
                logger.info(f"Detected {len(multiple_events)} sub-events in: {name}")
                # Add multiple events info to description for reference
                description += f"\n\n[Sadrži {len(multiple_events)} povezanih događanja]"

            return EventCreate(
                title=name,
                time=parsed_time,
                date=parsed_date,
                location=location,
                description=description,
                price=price,
                image=image_url,
                link=link,
                source="croatia",
                category=category if hasattr(EventCreate, 'category') else None,
            )

        except Exception as e:
            logger.error(f"Error transforming Croatia.hr event data: {e}")
            return None


class CroatiaPlaywrightScraper:
    """Scraper using Playwright for Croatia.hr dynamic content."""

    async def apply_comprehensive_filters(self, page) -> None:
        """Apply filters to get comprehensive event coverage."""
        try:
            logger.info("Applying comprehensive filters for better event coverage...")
            
            # Check if filters are available and interact with them
            filter_selectors = [
                'select[class*="region"]',
                'select[class*="county"]', 
                'select[class*="city"]',
                'select[class*="event-type"]',
                'input[class*="search"]',
                '.filter-dropdown',
                '.search-box'
            ]
            
            # Try to clear any existing filters first
            for selector in filter_selectors:
                try:
                    filter_element = await page.query_selector(selector)
                    if filter_element:
                        logger.info(f"Found filter element: {selector}")
                        # For select elements, set to "all" or first option
                        if selector.startswith('select'):
                            await filter_element.select_option(index=0)
                        # For input elements, clear them
                        elif selector.startswith('input'):
                            await filter_element.fill("")
                        
                        # Wait for filter results to load
                        await page.wait_for_timeout(2000)
                except Exception as e:
                    logger.debug(f"Could not interact with filter {selector}: {e}")
            
            # Try to expand view or show all events
            show_all_selectors = [
                'button:text("Prikaži sve")',
                'button:text("Show all")', 
                'button[class*="show-all"]',
                'button[class*="expand"]',
                '.show-more-button',
                '.load-all-button'
            ]
            
            for selector in show_all_selectors:
                try:
                    show_all = await page.query_selector(selector)
                    if show_all:
                        await show_all.click()
                        logger.info(f"Clicked show all button: {selector}")
                        await page.wait_for_timeout(3000)
                        break
                except Exception as e:
                    logger.debug(f"Could not click show all button {selector}: {e}")
            
        except Exception as e:
            logger.warning(f"Error applying comprehensive filters: {e}")

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
            if USE_PROXY and SCRAPING_CONFIG.is_websocket_endpoint:
                # Use WebSocket connection for Bright Data scraping browser
                logger.info(f"Connecting to Bright Data scraping browser: {BRD_WSS}")
                browser = await p.chromium.connect_over_cdp(BRD_WSS)
            elif USE_PROXY:
                # Use regular Chromium with proxy
                logger.info(f"Launching Chromium with proxy: {PROXY}")
                browser = await p.chromium.launch(proxy={"server": PROXY})
            else:
                # Local browser without proxy
                logger.info("Launching local Chromium browser")
                browser = await p.chromium.launch()

            page = await browser.new_page()

            try:
                logger.info(f"→ Fetching Croatia.hr events from {start_url}")
                await page.goto(start_url, wait_until="domcontentloaded", timeout=90000)

                # Enhanced Vue.js and API waiting logic
                logger.info("Waiting for Vue.js and API content to load...")
                
                # Wait for Vue.js framework to initialize
                await page.wait_for_function(
                    "window.Vue || document.querySelector('[data-v-]') || document.querySelector('.v-application')",
                    timeout=30000
                )
                
                # Wait for API calls to complete - look for content-service API responses
                logger.info("Waiting for Croatia.hr API responses...")
                try:
                    await page.wait_for_response(
                        lambda response: "content-service" in response.url or "dogadanja" in response.url,
                        timeout=20000
                    )
                    logger.info("API response detected, waiting for content rendering...")
                    await page.wait_for_timeout(3000)  # Allow content to render
                except Exception as e:
                    logger.warning(f"API response wait timeout: {e}, proceeding with fallback")
                    await page.wait_for_timeout(8000)  # Extended fallback wait
                
                # Try multiple strategies to wait for event containers
                event_selectors = [
                    '[class*="event"]',
                    '[class*="card"]', 
                    '[class*="item"]',
                    'a[href*="/dogadanja/"]',
                    '[class*="mosaic"]',
                    '[data-module*="event"]'
                ]
                
                for selector in event_selectors:
                    try:
                        await page.wait_for_selector(selector, timeout=10000)
                        logger.info(f"Events found with selector: {selector}")
                        break
                    except Exception:
                        continue
                else:
                    logger.warning("No event containers found with standard selectors, using fallback")
                
                # Apply filters to get comprehensive coverage
                await self.apply_comprehensive_filters(page)

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

    async def save_events_to_database(self, events: List[EventCreate]) -> int:
        """Save events to database with geocoding and return count of saved events."""
        if not events:
            return 0

        # First, geocode all event locations
        try:
            locations_to_geocode = [(event.location, "") for event in events if event.location]
            logger.info(f"Geocoding {len(locations_to_geocode)} event locations...")
            
            geocoding_results = await geocoding_service.batch_geocode_venues(locations_to_geocode)
            geocoded_count = len(geocoding_results)
            logger.info(f"Successfully geocoded {geocoded_count}/{len(locations_to_geocode)} locations")
            
        except Exception as e:
            logger.warning(f"Geocoding failed, continuing without coordinates: {e}")
            geocoding_results = {}

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
                    # Create event with explicit timestamps and geocoding
                    current_time = datetime.now()
                    event_dict = event_data.model_dump()
                    event_dict['created_at'] = current_time
                    event_dict['updated_at'] = current_time
                    
                    # Add geocoding coordinates if available
                    if event_data.location in geocoding_results:
                        result = geocoding_results[event_data.location]
                        event_dict['latitude'] = result.latitude
                        event_dict['longitude'] = result.longitude
                        logger.debug(f"Added coordinates for {event_data.location}: {result.latitude}, {result.longitude}")
                    
                    db_event = Event(**event_dict)
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
        saved_count = await scraper.save_events_to_database(events)

        return {
            "status": "success",
            "scraped_events": len(events),
            "saved_events": saved_count,
            "message": f"Successfully scraped {len(events)} events from Croatia.hr, saved {saved_count} new events",
        }

    except Exception as e:
        return {"status": "error", "message": f"Croatia.hr scraping failed: {str(e)}"}
