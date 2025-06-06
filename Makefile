# Diidemo.hr - Croatian Events Platform
# Comprehensive Makefile for development, testing, and deployment

.PHONY: help install dev build test lint format clean docker-build docker-up docker-down docker-logs docker-clean setup-db backup-db restore-db

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
BLUE = \033[0;34m
MAGENTA = \033[0;35m
CYAN = \033[0;36m
NC = \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

##@ Help
help: ## Show this help message
	@echo "$(CYAN)Diidemo.hr - Croatian Events Platform$(NC)"
	@echo "$(YELLOW)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(CYAN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Development Setup
install: ## Install all dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@npm install
	@cd frontend && npm install
	@cd backend && uv sync
	@echo "$(GREEN)✓ Dependencies installed successfully$(NC)"

install-tools: ## Install development tools (uv, docker, etc.)
	@echo "$(GREEN)Installing development tools...$(NC)"
	@command -v uv >/dev/null 2>&1 || (echo "Installing uv..." && curl -LsSf https://astral.sh/uv/install.sh | sh)
	@command -v docker >/dev/null 2>&1 || (echo "$(RED)Please install Docker manually$(NC)" && exit 1)
	@echo "$(GREEN)✓ Development tools ready$(NC)"

setup: install setup-db ## Complete project setup
	@echo "$(GREEN)✓ Project setup completed$(NC)"

##@ Database Operations
setup-db: ## Initialize database with sample data
	@echo "$(GREEN)Setting up database...$(NC)"
	@cd backend && uv run python scripts/setup_database.py
	@echo "$(GREEN)✓ Database initialized with sample Croatian events$(NC)"

backup-db: ## Backup database
	@echo "$(GREEN)Creating database backup...$(NC)"
	@mkdir -p backups
	@docker exec diidemo-postgres pg_dump -U postgres kruzna_karta_hrvatska > backups/backup_$(shell date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)✓ Database backed up to backups/$(NC)"

restore-db: ## Restore database from latest backup (usage: make restore-db BACKUP=filename.sql)
	@echo "$(GREEN)Restoring database...$(NC)"
	@if [ -z "$(BACKUP)" ]; then \
		echo "$(RED)Please specify backup file: make restore-db BACKUP=filename.sql$(NC)"; \
		exit 1; \
	fi
	@docker exec -i diidemo-postgres psql -U postgres -d kruzna_karta_hrvatska < backups/$(BACKUP)
	@echo "$(GREEN)✓ Database restored from $(BACKUP)$(NC)"

##@ Development
dev: ## Start development servers (frontend + backend)
	@echo "$(GREEN)Starting development servers...$(NC)"
	@npm run dev

dev-frontend: ## Start only frontend development server
	@echo "$(GREEN)Starting frontend development server...$(NC)"
	@cd frontend && npm run dev

dev-backend: ## Start only backend development server
	@echo "$(GREEN)Starting backend development server...$(NC)"
	@cd backend && uv run python run.py

##@ Code Quality
lint: lint-frontend lint-backend ## Run linting for all components
	@echo "$(GREEN)✓ All linting completed$(NC)"

lint-frontend: ## Lint frontend code
	@echo "$(YELLOW)Linting frontend...$(NC)"
	@cd frontend && npm run lint

lint-backend: ## Lint backend code
	@echo "$(YELLOW)Linting backend...$(NC)"
	@cd backend && uv run flake8 app/ --max-line-length=88 --extend-ignore=E203,W503
	@cd backend && uv run mypy app/ --ignore-missing-imports

format: format-frontend format-backend ## Format all code
	@echo "$(GREEN)✓ All code formatted$(NC)"

format-frontend: ## Format frontend code
	@echo "$(YELLOW)Formatting frontend code...$(NC)"
	@cd frontend && npx prettier --write "src/**/*.{ts,tsx,js,jsx,css,md}"
	@cd frontend && npm run lint -- --fix

format-backend: ## Format backend code
	@echo "$(YELLOW)Formatting backend code...$(NC)"
	@cd backend && uv run black app/ --line-length=88
	@cd backend && uv run isort app/ --profile=black

typecheck: ## Run TypeScript type checking
	@echo "$(YELLOW)Running type checks...$(NC)"
	@cd frontend && npx tsc --noEmit
	@cd backend && uv run mypy app/ --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking completed$(NC)"

##@ Testing
test: test-frontend test-backend ## Run all tests
	@echo "$(GREEN)✓ All tests completed$(NC)"

test-frontend: ## Run frontend tests
	@echo "$(YELLOW)Running frontend tests...$(NC)"
	@cd frontend && npm test

test-backend: ## Run backend tests
	@echo "$(YELLOW)Running backend tests...$(NC)"
	@cd backend && uv run pytest -v

test-coverage: ## Run tests with coverage report
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	@cd backend && uv run pytest --cov=app --cov-report=html --cov-report=term

test-integration: ## Run integration tests
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@cd backend && uv run pytest tests/integration/ -v

##@ Building
build: build-frontend build-backend ## Build all components
	@echo "$(GREEN)✓ All components built$(NC)"

build-frontend: ## Build frontend for production
	@echo "$(YELLOW)Building frontend...$(NC)"
	@cd frontend && npm run build

build-backend: ## Build backend for production
	@echo "$(YELLOW)Building backend...$(NC)"
	@cd backend && uv build

##@ Docker Operations
docker-build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	@docker compose build
	@echo "$(GREEN)✓ Docker images built successfully$(NC)"

docker-up: ## Start all services with Docker
	@echo "$(GREEN)Starting Docker services...$(NC)"
	@docker compose up -d
	@echo "$(GREEN)✓ Services started. Access at:$(NC)"
	@echo "  $(CYAN)Frontend:$(NC) http://localhost:3000"
	@echo "  $(CYAN)Backend:$(NC)  http://localhost:8000"
	@echo "  $(CYAN)API Docs:$(NC) http://localhost:8000/docs"

docker-up-build: ## Build and start all services
	@echo "$(GREEN)Building and starting Docker services...$(NC)"
	@docker compose up --build -d
	@echo "$(GREEN)✓ Services built and started$(NC)"

docker-down: ## Stop all Docker services
	@echo "$(YELLOW)Stopping Docker services...$(NC)"
	@docker compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-restart: ## Restart all Docker services
	@echo "$(YELLOW)Restarting Docker services...$(NC)"
	@docker compose restart
	@echo "$(GREEN)✓ Services restarted$(NC)"

docker-logs: ## Show Docker logs
	@docker compose logs -f

docker-logs-backend: ## Show backend logs
	@docker compose logs -f backend

docker-logs-frontend: ## Show frontend logs
	@docker compose logs -f frontend

docker-status: ## Show Docker services status
	@docker compose ps

docker-clean: ## Clean Docker containers and images
	@echo "$(YELLOW)Cleaning Docker containers and images...$(NC)"
	@docker compose down -v --rmi all --remove-orphans
	@docker system prune -f
	@echo "$(GREEN)✓ Docker cleaned$(NC)"

##@ Production Deployment
deploy-staging: ## Deploy to staging environment
	@echo "$(GREEN)Deploying to staging...$(NC)"
	@docker compose -f docker-compose.yml -f docker-compose.staging.yml up --build -d
	@echo "$(GREEN)✓ Deployed to staging$(NC)"

deploy-prod: ## Deploy to production environment
	@echo "$(GREEN)Deploying to production...$(NC)"
	@docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
	@echo "$(GREEN)✓ Deployed to production$(NC)"

##@ Maintenance
clean: ## Clean build artifacts and dependencies
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf frontend/dist frontend/node_modules/.cache
	@rm -rf backend/dist backend/.pytest_cache backend/__pycache__
	@rm -rf backend/app/__pycache__ backend/app/**/__pycache__
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned build artifacts$(NC)"

clean-all: clean docker-clean ## Clean everything including Docker
	@echo "$(YELLOW)Cleaning all dependencies...$(NC)"
	@rm -rf frontend/node_modules
	@rm -rf backend/.venv
	@rm -rf node_modules
	@echo "$(GREEN)✓ Cleaned all dependencies$(NC)"

reset: clean-all install ## Reset project (clean + reinstall)
	@echo "$(GREEN)✓ Project reset completed$(NC)"

##@ Scraping Operations
scrape-entrio: ## Quick scrape from Entrio.hr
	@echo "$(YELLOW)Scraping events from Entrio.hr...$(NC)"
	@curl -X GET "http://localhost:8000/api/scraping/entrio/quick?max_pages=2"

scrape-croatia: ## Quick scrape from Croatia.hr
	@echo "$(YELLOW)Scraping events from Croatia.hr...$(NC)"
	@curl -X GET "http://localhost:8000/api/scraping/croatia/quick?max_pages=2"

scrape-all: ## Scrape from all sources
	@echo "$(YELLOW)Scraping events from all sources...$(NC)"
	@curl -X POST "http://localhost:8000/api/scraping/all" \
		-H "Content-Type: application/json" \
		-d '{"max_pages": 3}'

##@ Monitoring
health-check: ## Check health of all services
	@echo "$(YELLOW)Checking service health...$(NC)"
	@echo "$(CYAN)Frontend:$(NC)"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 && echo " ✓" || echo " ✗"
	@echo "$(CYAN)Backend:$(NC)"
	@curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health && echo " ✓" || echo " ✗"
	@echo "$(CYAN)Database:$(NC)"
	@docker exec diidemo-postgres pg_isready -U postgres && echo " ✓" || echo " ✗"

monitor: ## Monitor application logs in real-time
	@echo "$(GREEN)Monitoring application logs...$(NC)"
	@docker compose logs -f --tail=100

##@ API Operations
api-docs: ## Open API documentation
	@echo "$(GREEN)Opening API documentation...$(NC)"
	@open http://localhost:8000/docs 2>/dev/null || xdg-open http://localhost:8000/docs 2>/dev/null || echo "Visit: http://localhost:8000/docs"

api-test: ## Test API endpoints
	@echo "$(YELLOW)Testing API endpoints...$(NC)"
	@echo "$(CYAN)Health check:$(NC)"
	@curl -s http://localhost:8000/health
	@echo "\n$(CYAN)Events endpoint:$(NC)"
	@curl -s http://localhost:8000/api/events | head -c 200
	@echo "..."

##@ Environment
env-check: ## Check environment setup
	@echo "$(YELLOW)Checking environment...$(NC)"
	@echo "$(CYAN)Node.js:$(NC) $$(node --version 2>/dev/null || echo 'Not installed')"
	@echo "$(CYAN)npm:$(NC) $$(npm --version 2>/dev/null || echo 'Not installed')"
	@echo "$(CYAN)Python:$(NC) $$(python3 --version 2>/dev/null || echo 'Not installed')"
	@echo "$(CYAN)uv:$(NC) $$(uv --version 2>/dev/null || echo 'Not installed')"
	@echo "$(CYAN)Docker:$(NC) $$(docker --version 2>/dev/null || echo 'Not installed')"
	@echo "$(CYAN)Docker Compose:$(NC) $$(docker compose version 2>/dev/null || echo 'Not installed')"

env-setup: ## Create environment files from templates
	@echo "$(YELLOW)Setting up environment files...$(NC)"
	@[ ! -f .env ] && cp .env.example .env || echo ".env already exists"
	@[ ! -f frontend/.env ] && cp frontend/.env.example frontend/.env 2>/dev/null || echo "frontend/.env not needed"
	@[ ! -f backend/.env ] && cp backend/.env.example backend/.env 2>/dev/null || echo "backend/.env not needed"
	@echo "$(GREEN)✓ Environment files created$(NC)"

##@ Git Operations
git-hooks: ## Install git hooks
	@echo "$(YELLOW)Installing git hooks...$(NC)"
	@cp scripts/pre-commit .git/hooks/ 2>/dev/null || echo "No pre-commit hook found"
	@chmod +x .git/hooks/pre-commit 2>/dev/null || true
	@echo "$(GREEN)✓ Git hooks installed$(NC)"

##@ Quick Actions
quick-start: env-setup docker-up-build ## Quick start for new developers
	@echo "$(GREEN)🚀 Diidemo.hr is ready!$(NC)"
	@echo "$(CYAN)Access your application:$(NC)"
	@echo "  • Frontend: http://localhost:3000"
	@echo "  • Backend:  http://localhost:8000"
	@echo "  • API Docs: http://localhost:8000/docs"

full-setup: install-tools install env-setup setup-db docker-build ## Complete setup from scratch
	@echo "$(GREEN)✓ Full setup completed$(NC)"

demo: quick-start health-check scrape-entrio ## Demo setup with sample data
	@echo "$(GREEN)🎉 Demo environment ready with sample data!$(NC)"

##@ Information
version: ## Show version information
	@echo "$(CYAN)Diidemo.hr - Croatian Events Platform$(NC)"
	@echo "Version: 1.0.0"
	@echo "Environment: $$([ -f .env ] && echo 'Configured' || echo 'Not configured')"
	@echo "Docker: $$(docker compose ps --format 'table {{.Service}}\t{{.State}}' 2>/dev/null || echo 'Not running')"

ports: ## Show used ports
	@echo "$(CYAN)Application Ports:$(NC)"
	@echo "  3000 - Frontend (React)"
	@echo "  8000 - Backend (FastAPI)"
	@echo "  5432 - PostgreSQL Database"
	@echo "  6379 - Redis Cache"
	@echo "  80   - Nginx Proxy"