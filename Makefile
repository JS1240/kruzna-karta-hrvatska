# Kruzna Karta Hrvatska - Croatian Events Platform
# Simplified Makefile for development and deployment

.PHONY: help install dev build test lint format clean docker-build docker-up docker-down docker-logs db-setup

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
CYAN = \033[0;36m
NC = \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

##@ Help
help: ## Show this help message
	@echo "$(CYAN)Kruzna Karta Hrvatska - Croatian Events Platform$(NC)"
	@echo "$(YELLOW)Available commands:$(NC)"
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make $(CYAN)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(CYAN)%-15s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup
install: ## Install all dependencies
	@echo "$(GREEN)Installing dependencies...$(NC)"
	@npm install
	@cd frontend-new && npm install
	@cd backend && uv sync
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

setup: install db-setup ## Complete project setup
	@echo "$(GREEN)✓ Project setup completed$(NC)"

##@ Development
dev: ## Start development servers (frontend + backend)
	@echo "$(GREEN)Starting development servers...$(NC)"
	@npm run dev

frontend-dev: ## Start only frontend development server
	@echo "$(GREEN)Starting frontend development server...$(NC)"
	@cd frontend-new && npm run dev

backend-dev: ## Start only backend development server
	@echo "$(GREEN)Starting backend development server...$(NC)"
	@cd backend && uv run python run.py

##@ Code Quality
lint: ## Run linting for all components
	@echo "$(YELLOW)Linting frontend...$(NC)"
	@cd frontend-new && npm run lint
	@echo "$(YELLOW)Linting backend...$(NC)"
	@cd backend && uv run ruff check app/
	@echo "$(GREEN)✓ All linting completed$(NC)"

format: ## Format all code
	@echo "$(YELLOW)Formatting frontend...$(NC)"
	@cd frontend-new && npm run format
	@echo "$(YELLOW)Formatting backend...$(NC)"
	@cd backend && uv run ruff format app/
	@echo "$(GREEN)✓ All code formatted$(NC)"

typecheck: ## Run TypeScript type checking
	@echo "$(YELLOW)Running type checks...$(NC)"
	@cd frontend-new && npm run typecheck
	@cd backend && uv run mypy app/ --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking completed$(NC)"

##@ Testing
test: ## Run all tests
	@echo "$(YELLOW)Running backend tests...$(NC)"
	@cd backend && uv run pytest -v
	@echo "$(GREEN)✓ All tests completed$(NC)"

##@ Building
build: ## Build all components
	@echo "$(YELLOW)Building frontend...$(NC)"
	@cd frontend-new && npm run build
	@echo "$(GREEN)✓ Build completed$(NC)"

##@ Docker Operations
docker-build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	@docker compose build
	@echo "$(GREEN)✓ Docker images built$(NC)"

docker-up: ## Start all services with Docker
	@echo "$(GREEN)Starting Docker services...$(NC)"
	@docker compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "  $(CYAN)Frontend:$(NC) http://localhost:3000"
	@echo "  $(CYAN)Backend:$(NC)  http://localhost:8000"
	@echo "  $(CYAN)API Docs:$(NC) http://localhost:8000/docs"

docker-down: ## Stop all Docker services
	@echo "$(YELLOW)Stopping Docker services...$(NC)"
	@docker compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

logs: ## Show all Docker logs
	@docker compose logs -f

frontend-logs: ## Show frontend logs
	@docker compose logs -f frontend

backend-logs: ## Show backend logs
	@docker compose logs -f backend

##@ Database
db-setup: ## Initialize database with sample data
	@echo "$(GREEN)Setting up database...$(NC)"
	@cd backend && uv run python scripts/setup_database.py
	@echo "$(GREEN)✓ Database initialized$(NC)"

db-shell: ## Access PostgreSQL shell
	@docker exec -it diidemo-postgres psql -U postgres -d kruzna_karta_hrvatska

redis-shell: ## Access Redis CLI
	@docker exec -it diidemo-redis redis-cli

##@ Maintenance
clean: ## Clean build artifacts
	@echo "$(YELLOW)Cleaning build artifacts...$(NC)"
	@rm -rf frontend-new/dist frontend-new/node_modules/.cache
	@rm -rf backend/.pytest_cache backend/__pycache__
	@find backend -name "*.pyc" -delete
	@find backend -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned build artifacts$(NC)"

reset: clean ## Reset project (clean + reinstall)
	@echo "$(YELLOW)Resetting project...$(NC)"
	@rm -rf frontend-new/node_modules backend/.venv node_modules
	@$(MAKE) install
	@echo "$(GREEN)✓ Project reset completed$(NC)"

##@ Quick Actions
start: docker-up ## Quick start all services
	@echo "$(GREEN)🚀 All services started!$(NC)"

stop: docker-down ## Quick stop all services

restart: docker-down docker-up ## Restart all services

status: ## Show Docker services status
	@docker compose ps

##@ Utilities
migrate: ## Run database migrations
	@echo "$(YELLOW)Running database migrations...$(NC)"
	@cd backend && uv run alembic upgrade head
	@echo "$(GREEN)✓ Migrations completed$(NC)"

migration: ## Create new migration (usage: make migration name="description")
	@echo "$(YELLOW)Creating new migration...$(NC)"
	@cd backend && uv run alembic revision --autogenerate -m "$(name)"
	@echo "$(GREEN)✓ Migration created$(NC)"