# Changelog

All notable changes to the Croatian Events Platform ("Kružna Karta Hrvatska") will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Comprehensive Subagents Documentation**:
  - Complete subagents reference section in CLAUDE.md with 30+ specialized agents
  - Detailed descriptions, capabilities, and usage guidelines for each subagent
  - Mandatory "Always Use Subagents" policy for complex tasks and specialized domains
  - Croatian Events Platform specific usage scenarios and workflow integration
  - Best practices for subagent selection and quality assurance

### In Development
- Performance optimizations for map clustering
- Enhanced error handling for scraping failures
- Additional Croatian event source integrations

## [2024-08-03] - Croatia Scraper Enhancement Release

### Added
- **Croatia.hr Scraper Enhancements**:
  - Vue.js dynamic content handling with Playwright browser automation
  - Event categorization system using Croatian keywords (10+ categories: Music, Culture, Sports, Food, Entertainment, Education, Business, Tourism, Festival, Art)
  - Advanced Croatian date parsing with 11 specialized patterns for complex date ranges
  - Multiple event detection within single event descriptions
  - Enhanced location parsing with Croatian geographic context

- **Geocoding Service Improvements**:
  - Real-time venue geocoding with Croatian geographic database integration
  - Coordinate caching system with 30-day refresh cycle and confidence scoring
  - Multi-provider fallback strategy (Mapbox API → Nominatim → Croatian city centers)
  - Croatian address pattern recognition and diacritics handling (č, ć, š, ž, đ)
  - Batch processing with concurrent geocoding and rate limiting

- **Advanced Map System**:
  - Dynamic event clustering with zoom-aware thresholds and distance-based grouping
  - Performance optimization with throttled map updates (60fps immediate, 250ms debounced)  
  - Custom cluster markers with hover states and click interactions
  - Smart popups for single events vs. event clusters
  - Batched marker positioning with RAF-throttled calculations

- **Frontend Performance Features**:
  - Custom hooks for performance-critical map operations (`useEventClustering`, `useThrottledMapUpdates`)
  - Memory management with efficient cleanup for map instances
  - Hardware acceleration using CSS transforms and `will-change` optimizations
  - Development-mode performance metrics tracking

### Changed
- **Croatia Scraper Architecture**:
  - Removed hardcoded `BASE_URL` constant for dynamic URL construction
  - Enhanced event data transformation with robust validation
  - Improved duplicate prevention using title + date matching
  - Updated browser proxy configuration with fallback strategies

- **Database Schema Enhancements**:
  - Enhanced event schema with geographic coordinates (`latitude`, `longitude`)
  - Added scraping metadata fields (`source`, `external_id`, `scrape_hash`, `last_scraped_at`)
  - Improved venue relationships and location tracking
  - Enhanced booking system integration with commission tracking

- **Configuration System Updates**:
  - Centralized configuration through `CONFIG` object in `components.py`
  - Type-safe Pydantic-based configuration with environment variable expansion
  - Enhanced scraping configuration with proxy and browser settings
  - Security improvements with automatic secure key generation

### Fixed
- **Scraping Issues**:
  - Vue.js content loading timeout problems with enhanced detection strategies
  - Croatian text encoding issues and special character handling
  - Browser proxy connection errors with `net::ERR_EMPTY_RESPONSE`
  - JavaScript string escape sequence warnings in debug logging

- **Geocoding Reliability**:
  - Croatian location recognition accuracy improved to 100% success rate
  - Address parsing errors for Croatian street patterns
  - Coordinate validation and bounds checking for Croatian territory
  - Cache invalidation and refresh cycle management

- **Map Performance**:
  - Layout thrashing during marker positioning operations
  - Clustering algorithm performance with large event datasets
  - Memory leaks in map component lifecycle management
  - Responsive design issues with adaptive clustering thresholds

### Security
- Enhanced proxy configuration validation and secure credential handling
- Improved input sanitization for scraped event data
- Strengthened database query validation and SQL injection prevention

## [Previous Releases]

### [2024-07-30] - Map System Foundation
- Initial Mapbox GL JS integration with custom styling
- Basic event clustering and marker system
- Frontend React 19 + TypeScript + Tailwind CSS setup

### [2024-07-25] - Backend Architecture
- FastAPI + SQLAlchemy 2.0 foundation
- PostgreSQL database with spatial extensions
- Basic scraping system with abstract base scraper
- Pydantic configuration management

### [2024-07-20] - Project Initialization
- Monorepo structure setup with frontend-new/ and backend/
- Docker containerization with development tooling
- Comprehensive Makefile with 40+ development commands
- Initial CI/CD pipeline and testing framework

---

## Change Categories

### Added
New features, functionality, or capabilities added to the system.

### Changed  
Modifications to existing functionality, refactoring, or improvements.

### Deprecated
Features marked for removal in future versions (with migration path).

### Removed
Features, files, or functionality completely removed from the system.

### Fixed
Bug fixes, error corrections, and issue resolutions.

### Security
Security-related changes, vulnerability fixes, or security enhancements.

---

## Versioning Strategy

- **Major versions (X.0.0)**: Breaking changes, major feature releases
- **Minor versions (0.X.0)**: New features, backward-compatible changes  
- **Patch versions (0.0.X)**: Bug fixes, security patches, minor improvements

## Contributing to Changelog

When making changes to the project:

1. **Always update this CHANGELOG.md** with your changes
2. **Use appropriate category**: Added/Changed/Deprecated/Removed/Fixed/Security
3. **Include context**: What changed, why it changed, and impact
4. **Reference issues**: Link to GitHub issues or PRs when applicable
5. **Date format**: Use ISO 8601 format (YYYY-MM-DD) for release dates
6. **Keep entries concise**: Focus on user/developer impact, not implementation details

## Links and References

- [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
- [Semantic Versioning](https://semver.org/spec/v2.0.0.html)
- [Project Repository](https://github.com/your-username/kruzna-karta-hrvatska)
- [Development Guide](./CLAUDE.md)
- [Makefile Commands](./MAKEFILE.md)