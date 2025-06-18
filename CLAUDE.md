# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a full-stack Croatian events platform ("Kružna Karta Hrvatska") built as a monorepo with:
- **Frontend**: React 18 + TypeScript + Tailwind CSS + Vite
- **Backend**: FastAPI + Python + PostgreSQL + Redis
- **Infrastructure**: Docker, Nginx, monitoring with Uptime Kuma

The platform aggregates events from multiple Croatian websites through web scraping and provides a unified booking experience with integrated payments.

## Key Architecture

### Monorepo Structure
- `frontend/` - React TypeScript application
- `backend/` - FastAPI Python application  
- `docker/` - Docker configurations and infrastructure
- `monitoring/` - Uptime Kuma monitoring setup

### Technology Stack
- **Frontend**: React 18, TypeScript, Tailwind CSS, React Router, React Query, Leaflet maps
- **Backend**: FastAPI, SQLAlchemy, Alembic, Celery, Redis, Playwright (web scraping)
- **Database**: PostgreSQL with Redis for caching/sessions
- **Deployment**: Docker Compose, Nginx reverse proxy

## Development Commands

The project uses a comprehensive Makefile with 40+ commands. Key commands:

### Quick Start
```bash
make setup           # Initial project setup
make dev            # Start full development environment
make frontend-dev   # Frontend only
make backend-dev    # Backend only
```

### Daily Development
```bash
make logs           # View all logs
make frontend-logs  # Frontend logs only
make backend-logs   # Backend logs only
make db-shell      # PostgreSQL shell access
make redis-shell   # Redis CLI access
```

### Code Quality
```bash
make lint          # Run all linters
make test          # Run all tests
make frontend-test # Frontend tests only
make backend-test  # Backend tests with coverage
```

### Database Management
```bash
make migrate       # Run database migrations
make migration     # Create new migration
make db-reset     # Reset database with sample data
```

## Key Business Logic

### Web Scraping System
- Scrapes 8+ Croatian event websites using Playwright
- Located in `backend/app/scraping/`
- Handles multiple site structures and formats
- Stores events with deduplication logic

### Event Management
- Events stored with venue, pricing, and scheduling data
- Booking system with seat selection where applicable
- Integration with payment processors
- Platform commission of 5% applied to all bookings

### Multi-language Support
- Croatian (hr) and English (en) supported
- Translation files in `frontend/src/locales/`
- Backend API serves localized content

## Development Guidelines

### Frontend Patterns
- Components in `frontend/src/components/`
- Pages in `frontend/src/pages/`
- Hooks for API calls using React Query
- Tailwind for styling with custom theme
- TypeScript strict mode enabled

### Backend Patterns
- FastAPI with dependency injection
- SQLAlchemy ORM with Alembic migrations
- Pydantic models for API serialization
- Celery for background tasks (scraping, emails)
- JWT authentication with Redis sessions

### Environment Setup
- Frontend env: `frontend/.env` (API_URL, maps config)
- Backend env: `backend/.env` (database, Redis, secrets)
- Docker env: `docker/.env` (ports, volumes)

### Testing
- Frontend: Vitest + React Testing Library
- Backend: pytest with fixtures and database isolation
- Run `make test` for full test suite

### Database Migrations
- Use `make migration name="description"` to create migrations
- Always review generated migrations before applying
- Use `make migrate` to apply pending migrations

## Common Tasks

### Adding New Event Source
1. Create scraper in `backend/app/scraping/scrapers/`
2. Add URL patterns to scraper registry
3. Test with `make scrape-test`
4. Update documentation

### API Development
- Add routes in `backend/app/api/routes/`
- Use dependency injection for database access
- Add Pydantic schemas in `backend/app/schemas/`
- Follow existing patterns for error handling

### Frontend Components
- Use TypeScript interfaces for props
- Follow existing component structure
- Use React Query for data fetching
- Implement responsive design with Tailwind

## Infrastructure

### Local Development
- All services run via Docker Compose
- Frontend dev server proxies API calls
- Hot reload enabled for both frontend and backend
- PostgreSQL and Redis run in containers

### Production Deployment
- Docker Compose with production configurations
- Nginx reverse proxy handles routing
- SSL termination and static file serving
- Environment-specific configurations

## Troubleshooting

### Common Issues
- Port conflicts: Check `docker/.env` for port assignments
- Database connection: Ensure PostgreSQL container is running
- Migration failures: Check migration files and database state
- Scraping issues: Verify Playwright browser installation

### Useful Debug Commands
```bash
make shell          # Backend Python shell
make frontend-shell # Frontend container shell
make db-logs       # Database logs
make nginx-logs    # Nginx logs
```