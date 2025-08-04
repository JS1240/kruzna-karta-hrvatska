# Key Business Logic

This document details the core business logic and technical architecture of the Croatian Events Platform ("Kružna Karta Hrvatska").

## Enhanced Scraping System

**Multi-Source Event Scraping**:
- **Base Architecture**: Abstract base scraper with common functionality for retry logic, date parsing, and text cleaning
- **BrightData Integration**: Proxy support with scraping browser for JavaScript-heavy sites
- **Playwright Support**: Dynamic content scraping for Vue.js/React applications
- **Specialized Scrapers**: 14+ Croatian event sources including Croatia.hr, Entrio, Info Zagreb, city tourism sites
- **Data Transformation**: Croatian date/time parsing, location extraction, and event normalization
- **Deduplication**: Hash-based duplicate detection and event merging

**Supported Event Sources**:
- `croatia_scraper.py` - Croatia.hr official tourism events (Vue.js-based)
- `entrio_scraper.py` - Entrio ticketing platform
- `infozagreb_scraper.py` - Zagreb city events
- City tourism sites: Split, Rijeka, Dubrovnik, Karlovac, Opatija, Varaždin, Vukovar, Zadar
- `ulaznice_scraper.py` - Ulaznice.hr ticketing platform

## Advanced Geocoding and Location Services

**Real-time Geocoding Service**:
- **Multi-Provider Strategy**: Mapbox API primary, Nominatim (OpenStreetMap) fallback
- **Croatian Geographic Database**: Built-in database of 70+ Croatian cities, regions, and landmarks with coordinates
- **Venue Coordinate Caching**: Database caching of geocoded venues with 30-day refresh cycle
- **Fallback Strategies**: Croatian city center fallback, Zagreb coordinates as ultimate fallback
- **Address Enhancement**: Croatian address pattern recognition and street-level geocoding
- **Batch Processing**: Concurrent geocoding with rate limiting and retry logic

**Croatian Geographic Coverage**:
- Major cities: Zagreb, Split, Rijeka, Osijek, Zadar, Pula, Dubrovnik
- Tourist destinations: Hvar, Korčula, Krk, Rovinj, Opatija, Makarska
- Regional centers and counties with population-based confidence scoring
- Fuzzy matching for Croatian diacritics (č, ć, š, ž, đ)

## Configuration System

**Type-Safe Configuration Management**:
- **Pydantic Settings**: Full type validation with automatic environment variable binding
- **YAML Configuration**: `backend/config.yaml` with environment variable expansion (`${VAR:default}`)
- **Component-Based Structure**: Database, Redis, API, Auth, Scraping, Services, Monitoring configs
- **Security**: Automatic secure key generation, insecure value detection, minimum security requirements
- **Development**: Mock external APIs, debug options, database seeding flags

**Configuration Components**:
```python
# Access via centralized CONFIG object
from app.config.components import get_settings
CONFIG = get_settings()

# Type-safe access to all settings
database_url = CONFIG.database.url
scraping_config = CONFIG.scraping
geocoding_provider = CONFIG.services.geocoding.provider
```

## Event Management

- Events stored with venue, pricing, and scheduling data
- Booking system with seat selection where applicable
- Integration with payment processors
- Platform commission of 5% applied to all bookings

## Multi-language Support

- Croatian (hr) as primary language and English (en) as secondary
- Translation files in `frontend-new/src/locales/`
- Backend API serves localized content

## Database Schema Updates

**Enhanced Event Schema**:
- Geographic coordinates (`latitude`, `longitude`) with decimal precision
- Enhanced location tracking (`location`, `venue_id` relationships)
- Scraping metadata (`source`, `external_id`, `scrape_hash`, `last_scraped_at`)
- Event categorization and tagging systems
- Booking system integration with commission tracking

**New Tables**:
- `venue_coordinates` - Geocoding cache with confidence scoring and multiple data sources
- Additional analytics, booking, and social feature tables from migration system

**Geographic Extensions**:
- PostGIS/Earthdistance for geographic queries and distance calculations
- Spatial indexing for location-based event searches
- Croatian coordinate validation and bounds checking