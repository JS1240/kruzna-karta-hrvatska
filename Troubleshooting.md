# Troubleshooting

This document provides comprehensive troubleshooting guidance for the Croatian Events Platform ("Kružna Karta Hrvatska").

## Common Issues

- **Port conflicts**: Check `docker/.env` and root `package.json` for port assignments
- **Database connection**: Ensure PostgreSQL container with geocoding extensions is running
- **Migration failures**: Check Alembic migrations and geocoding table schemas
- **Scraping issues**: Verify Playwright browser installation and Croatian scraper configurations
- **Map rendering**: Ensure Mapbox access token is configured in `frontend-new/.env`
- **Geocoding failures**: Check geocoding service configuration and Croatian location database

## Enhanced Debug Commands

```bash
make help           # Show all 40+ available commands
make dev            # Start full development environment
make frontend-dev   # Frontend only with Mapbox (runs on port 3001)
make backend-dev    # Backend with geocoding services
make logs           # All service logs
make db-shell       # PostgreSQL with geocoding tables
make lint           # Frontend + backend linting
make test           # Comprehensive test suite
```

## Performance Optimization

- **Map Performance**: Use throttled updates and clustering for large event datasets
- **Geocoding**: Leverage caching and Croatian location database for faster lookups
- **Scraping**: Monitor scraper performance and adjust throttling as needed
- **Database**: Utilize spatial indexes and optimized geocoding queries