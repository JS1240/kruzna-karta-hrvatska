# Infrastructure

This document provides comprehensive infrastructure documentation for the Croatian Events Platform ("Kružna Karta Hrvatska").

## Local Development

- All services orchestrated via comprehensive Makefile commands
- Frontend dev server with HMR and Mapbox integration
- Backend with uv package management and real-time geocoding
- PostgreSQL with advanced geocoding tables and spatial extensions
- Redis for caching, sessions, and geocoding results

## Advanced Services

- **Geocoding Service**: Real-time venue coordinate resolution with Croatian geographic database
- **Scraping System**: 14+ specialized scrapers with intelligent error handling and performance monitoring
- **Map Clustering**: Dynamic event clustering with performance optimization and smooth transitions
- **Configuration Management**: Type-safe Pydantic configuration with environment variable expansion

## Production Deployment

- Docker Compose with optimized production configurations
- Nginx reverse proxy with static file serving and SSL termination
- Advanced database with geocoding tables and spatial queries
- Comprehensive monitoring and error handling across all services