# Diidemo.hr - Croatian Events Discovery Platform

A full-stack Croatian events platform built with React (frontend), FastAPI (backend), and PostgreSQL (database).

## 🚀 Quick Start with Makefile (Recommended)

### Prerequisites
- Docker and Docker Compose installed
- 4GB+ RAM available
- Ports 80, 3000, 8000, 5432, 6379 available

### 1. Clone and Setup
```bash
git clone <repository-url>
cd kruzna-karta-hrvatska
```

### 2. One-Command Setup
```bash
# Complete setup and start (recommended)
make quick-start

# Or step by step
make env-setup
make docker-up-build
```

### 3. Alternative: Manual Docker Setup
```bash
# Copy environment template
cp .env.example .env

# Build and start all services
docker-compose up --build

# Or run in background
docker-compose up -d --build
```

### 4. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (postgres/diidemo2024)

### 5. Docker Management
```bash
# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Reset database
docker-compose down -v && docker-compose up --build
```

## 🐳 Docker Architecture

### Container Stack
```
┌─────────────────┐
│   Nginx Proxy   │ :80
├─────────────────┤
│   Frontend      │ :3000 (React + Nginx)
├─────────────────┤
│   Backend API   │ :8000 (FastAPI + Python)
├─────────────────┤
│   PostgreSQL    │ :5432 (Database)
├─────────────────┤
│   Redis         │ :6379 (Cache)
└─────────────────┘
```

### Services
- **Frontend**: React + TypeScript + Vite served by Nginx
- **Backend**: FastAPI + SQLAlchemy + Python with uv
- **Database**: PostgreSQL 15 with sample Croatian events
- **Cache**: Redis 7 for caching and task queues
- **Proxy**: Nginx reverse proxy with load balancing

## 🏗️ Project Structure

```
kruzna-karta-hrvatska/
├── frontend/                 # React + TypeScript frontend
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/           # Page components
│   │   ├── lib/             # Utilities and API client
│   │   └── hooks/           # Custom React hooks
│   ├── public/              # Static assets
│   └── package.json         # Frontend dependencies
├── backend/                 # FastAPI Python backend
│   ├── app/
│   │   ├── routes/          # API endpoints
│   │   ├── models/          # Database models & schemas
│   │   ├── core/            # Configuration & database
│   │   └── main.py          # FastAPI application
│   ├── scripts/             # Database setup scripts
│   ├── pyproject.toml       # Python dependencies (uv)
│   └── run.py              # Development server runner
└── package.json            # Root package.json for monorepo
```

## 🚀 Quick Start

### Prerequisites

- **Node.js** >= 18.0.0
- **Python** >= 3.11.0
- **PostgreSQL** database
- **uv** package manager for Python

#### Install uv (Python package manager)
```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd kruzna-karta-hrvatska

# Install root dependencies (includes concurrently for running both servers)
npm install

# Setup backend and frontend dependencies
npm run setup
```

### 2. Database Setup

```bash
# 1. Create PostgreSQL database
createdb kruzna_karta_hrvatska

# 2. Copy environment files and configure
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# 3. Edit backend/.env with your database credentials:
# DATABASE_URL=postgresql://username:password@localhost:5432/kruzna_karta_hrvatska

# 4. Run database setup script
npm run setup:db
```

### 3. Start Development Servers

```bash
# Start both frontend and backend simultaneously
npm run dev

# Or start individually:
npm run dev:frontend  # Frontend at http://localhost:5173
npm run dev:backend   # Backend at http://localhost:8000
```

## 📁 Detailed Structure

### Frontend (`/frontend`)
- **React 18** with TypeScript
- **Vite** for fast development and building
- **Tailwind CSS** for styling
- **shadcn/ui** component library
- **React Router** for navigation
- **React Hook Form** with Zod validation
- **Mapbox** for interactive maps

### Backend (`/backend`)
- **FastAPI** Python web framework
- **SQLAlchemy** ORM for database operations
- **Pydantic** for data validation
- **PostgreSQL** database
- **uv** for dependency management
- **Uvicorn** ASGI server

### Database Schema

The `events` table includes:
- `id` (Primary Key)
- `name` (Event name)
- `time` (Event time)
- `date` (Event date)
- `location` (Event location)
- `description` (Event description)
- `price` (Ticket price)
- `image` (Event image URL)
- `link` (Ticket/event link)
- `created_at` & `updated_at` (Timestamps)

## 🕷️ Event Scraping System

The backend includes an integrated web scraping system that automatically collects events from Croatian event websites:

### Supported Sites
- **Entrio.hr** - Croatia's leading event ticketing platform
- **Croatia.hr** - Official Croatian tourism events portal
- **InfoZagreb.hr** - Zagreb tourist board event listings
- **VisitRijeka.hr** - Rijeka tourist board events
- **VisitKarlovac.hr** - Karlovac region events and attractions
- **VisitSplit.com** - Split city events and news


### Features
- **Dual Scraping Approach**: Uses both requests/BeautifulSoup and Playwright for maximum compatibility
- **BrightData Integration**: Supports proxy scraping through BrightData for reliable data collection
- **Automatic Data Processing**: Transforms scraped data to match database schema
- **Duplicate Prevention**: Automatically detects and prevents duplicate events
- **Scheduled Tasks**: Optional automatic scraping at configurable intervals

### Usage

#### Manual Scraping via API
```bash
# Quick scraping from Entrio.hr (1-3 pages)
curl -X GET "http://localhost:8000/api/scraping/entrio/quick?max_pages=2"

# Quick scraping from Croatia.hr (1-3 pages)
curl -X GET "http://localhost:8000/api/scraping/croatia/quick?max_pages=2"

# Quick scraping from InfoZagreb.hr (1-3 pages)
curl -X GET "http://localhost:8000/api/scraping/infozagreb/quick?max_pages=2"


# Quick scraping from VisitRijeka.hr (1-3 pages)
curl -X GET "http://localhost:8000/api/scraping/visitrijeka/quick?max_pages=2"

# Quick scraping from VisitKarlovac.hr (1-3 pages)
curl -X GET "http://localhost:8000/api/scraping/visitkarlovac/quick?max_pages=2"

# Quick scraping from VisitSplit.com (1-3 pages)
curl -X GET "http://localhost:8000/api/scraping/visitsplit/quick?max_pages=2"


# Full scraping from specific site (background task)
curl -X POST "http://localhost:8000/api/scraping/entrio" \
  -H "Content-Type: application/json" \
  -d '{"max_pages": 5, "use_playwright": true}'

# Full scraping from InfoZagreb.hr
curl -X POST "http://localhost:8000/api/scraping/infozagreb" \
  -H "Content-Type: application/json" \
  -d '{"max_pages": 5}'


# Full scraping from VisitRijeka.hr
curl -X POST "http://localhost:8000/api/scraping/visitrijeka" \

# Full scraping from VisitKarlovac.hr
curl -X POST "http://localhost:8000/api/scraping/visitkarlovac" \

  -H "Content-Type: application/json" \
  -d '{"max_pages": 5}'

# Full scraping from VisitSplit.com
curl -X POST "http://localhost:8000/api/scraping/visitsplit" \
  -H "Content-Type: application/json" \
  -d '{"max_pages": 5}'

# Scrape from ALL supported sites
curl -X POST "http://localhost:8000/api/scraping/all" \
  -H "Content-Type: application/json" \
  -d '{"max_pages": 3}'

# Check scraping status
curl -X GET "http://localhost:8000/api/scraping/status"
```

#### Automated Scraping
Enable in `.env`:
```env
ENABLE_SCHEDULER=true
```

**Schedules:**
- **Production**: Daily at 02:00 (10 pages per site)
- **Development**: Hourly (2 pages per site)

- **Sites**: Entrio.hr, Croatia.hr, InfoZagreb.hr and VisitRijeka.hr

- **Sites**: Entrio.hr, Croatia.hr, InfoZagreb.hr and VisitKarlovac.hr

- **Sites**: Entrio.hr, Croatia.hr, InfoZagreb.hr and VisitSplit.com


### Configuration

#### Basic Setup (No Proxy)
```env
USE_PLAYWRIGHT=true
USE_PROXY=false
```

#### With BrightData Proxy
```env
USE_PROXY=true
USE_PLAYWRIGHT=true
BRIGHTDATA_USER=your-user
BRIGHTDATA_PASSWORD=your-password
```

## 🔧 Development with Makefile

We provide a comprehensive Makefile for easy development, testing, and deployment. See [MAKEFILE.md](./MAKEFILE.md) for detailed documentation.

### Common Makefile Commands
```bash
make help            # Show all available commands
make dev             # Start development servers
make format          # Format all code
make lint            # Run linting
make test            # Run all tests
make docker-up       # Start with Docker
make clean           # Clean build artifacts
```

### Quick Development Workflow
```bash
make dev             # Start development
make format          # Format code before committing
make test            # Run tests
make health-check    # Verify everything works
```

## 🔧 Alternative: NPM Scripts

### Root Scripts
```bash
npm run dev          # Start both frontend and backend
npm run setup        # Setup all dependencies
npm run setup:db     # Initialize database with sample data
npm run build        # Build frontend for production
npm run lint         # Lint frontend code
```

### Frontend Scripts
```bash
cd frontend
npm run dev          # Start development server
npm run build        # Build for production
npm run lint         # Run ESLint
npm run preview      # Preview production build
```

### Backend Scripts
```bash
cd backend
uv run python run.py                    # Start development server
uv run uvicorn app.main:app --reload   # Alternative start method
uv run python scripts/setup_database.py # Setup database
uv run pytest                          # Run tests
```

## 🌐 API Endpoints

The backend provides RESTful API endpoints:

### Events
- `GET /api/events` - Get all events (with filtering & pagination)
- `GET /api/events/{id}` - Get specific event
- `POST /api/events` - Create new event
- `PUT /api/events/{id}` - Update event
- `DELETE /api/events/{id}` - Delete event
- `POST /api/user-events/create` - Submit a user-generated event (authentication required; new events are marked as pending until reviewed)

### Scraping
- `POST /api/scraping/entrio` - Trigger full Entrio.hr scraping
- `GET /api/scraping/entrio/quick` - Quick Entrio.hr scraping (1-3 pages)
- `POST /api/scraping/croatia` - Trigger full Croatia.hr scraping
- `GET /api/scraping/croatia/quick` - Quick Croatia.hr scraping (1-3 pages)
- `POST /api/scraping/infozagreb` - Trigger full InfoZagreb.hr scraping
- `GET /api/scraping/infozagreb/quick` - Quick InfoZagreb.hr scraping (1-3 pages)
- `POST /api/scraping/visitrijeka` - Trigger full VisitRijeka.hr scraping
- `GET /api/scraping/visitrijeka/quick` - Quick VisitRijeka.hr scraping (1-3 pages)
- `POST /api/scraping/visitkarlovac` - Trigger full VisitKarlovac.hr scraping
- `GET /api/scraping/visitkarlovac/quick` - Quick VisitKarlovac.hr scraping (1-3 pages)
- `POST /api/scraping/visitsplit` - Trigger full VisitSplit.com scraping
- `GET /api/scraping/visitsplit/quick` - Quick VisitSplit.com scraping (1-3 pages)
- `POST /api/scraping/all` - Scrape from all supported sites
- `GET /api/scraping/status` - Get scraping system status

### API Documentation
Visit http://localhost:8000/docs for interactive API documentation (Swagger UI).

## 🔐 Environment Variables

Create a `.env` file at the project root by copying `.env.example` and setting the values:

### `.env`
```env
POSTGRES_DB=kruzna_karta_hrvatska
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-postgres-password

DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB}
REDIS_URL=redis://redis:6379/0
SECRET_KEY=your-secret-key
DEBUG=true
FRONTEND_URL=http://localhost:3000

# Scraping Configuration
ENABLE_SCHEDULER=false
USE_PROXY=false
USE_PLAYWRIGHT=true
BRIGHTDATA_USER=your-brightdata-user
BRIGHTDATA_PASSWORD=your-brightdata-password

# Frontend
VITE_API_BASE_URL=http://localhost:8000/api
VITE_MAPBOX_ACCESS_TOKEN=your_mapbox_token_here
```

## 🧪 Testing

```bash
# Run backend tests
npm run test

# Run frontend tests (if configured)
cd frontend && npm test
```

## 📦 Production Deployment

### Backend
```bash
cd backend
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm run build
# Serve the dist/ directory with your preferred web server
```

### Docker Deployment

Build a single image that bundles the frontend, backend and nginx:

```bash
# Build the production image
docker build -t kruzna-karta-prod -f docker-prod/Dockerfile .

# Run the container
docker run -d -p 80:80 --env-file .env kruzna-karta-prod
```

The container exposes port `80` and serves both the API and the UI. Adjust the
`.env` file for your production settings before building the image.

Alternatively you can run the full stack with `docker compose`. This will
launch PostgreSQL, Redis and the application behind Nginx using the provided
compose definitions:

```bash
# Production stack with TLS
docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

For HTTPS support place your certificate files (`fullchain.pem` and
`privkey.pem`) inside the `ssl/` directory before starting the containers.

## 🛠️ Development

### Adding New Features

1. **Backend**: Add new routes in `backend/app/routes/`
2. **Frontend**: Create components in `frontend/src/components/`
3. **Database**: Update models in `backend/app/models/`

### Database Migrations

The project uses SQLAlchemy. For schema changes:

```bash
cd backend
# Create migration
uv run alembic revision --autogenerate -m "Description"
# Apply migration
uv run alembic upgrade head
```

### Adding a New Language

1. Place a new `<code>.json` file inside `frontend/src/i18n/` with your translations.
2. Add the language code to the `Language` type in `frontend/src/contexts/LanguageContext.tsx`.
3. Provide a UI option for switching to the new language.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.