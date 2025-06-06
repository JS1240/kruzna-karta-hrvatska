# 🛠️ Makefile Guide for Diidemo.hr

The Makefile provides a comprehensive set of commands for developing, testing, building, and deploying the Diidemo.hr Croatian Events Platform.

## 🚀 Quick Start

```bash
# Show all available commands
make help

# Complete setup for new developers
make quick-start

# Start development environment
make dev
```

## 📋 Command Categories

### 🏗️ Development Setup
- `make install` - Install all dependencies
- `make install-tools` - Install development tools (uv, docker, etc.)
- `make setup` - Complete project setup
- `make env-setup` - Create environment files from templates

### 💾 Database Operations
- `make setup-db` - Initialize database with sample data
- `make backup-db` - Create database backup
- `make restore-db BACKUP=filename.sql` - Restore from backup

### 🔧 Development
- `make dev` - Start both frontend and backend
- `make dev-frontend` - Start only frontend server
- `make dev-backend` - Start only backend server

### 🎨 Code Quality
- `make format` - Format all code (frontend + backend)
- `make lint` - Run linting for all components
- `make typecheck` - Run TypeScript type checking

### 🧪 Testing
- `make test` - Run all tests
- `make test-coverage` - Run tests with coverage report
- `make test-integration` - Run integration tests

### 📦 Building
- `make build` - Build all components for production
- `make build-frontend` - Build only frontend
- `make build-backend` - Build only backend

### 🐳 Docker Operations
- `make docker-up` - Start all services with Docker
- `make docker-up-build` - Build and start all services
- `make docker-down` - Stop all services
- `make docker-logs` - Show logs from all services
- `make docker-clean` - Clean containers and images

### 🌐 Production Deployment
- `make deploy-staging` - Deploy to staging environment
- `make deploy-prod` - Deploy to production environment

### 🕷️ Scraping Operations
- `make scrape-entrio` - Quick scrape from Entrio.hr
- `make scrape-croatia` - Quick scrape from Croatia.hr
- `make scrape-all` - Scrape from all sources

### 📊 Monitoring
- `make health-check` - Check health of all services
- `make monitor` - Monitor application logs
- `make api-docs` - Open API documentation

### 🧹 Maintenance
- `make clean` - Clean build artifacts
- `make clean-all` - Clean everything including dependencies
- `make reset` - Reset project (clean + reinstall)

## 💡 Common Workflows

### New Developer Setup
```bash
# Complete setup from scratch
make full-setup

# Or step by step
make install-tools
make install
make env-setup
make setup-db
make docker-build
```

### Daily Development
```bash
# Start development
make dev

# Format code before committing
make format

# Run tests
make test

# Check everything is working
make health-check
```

### Code Quality Workflow
```bash
# Format code
make format

# Run linting
make lint

# Run type checking
make typecheck

# Run tests
make test
```

### Docker Development
```bash
# Start with Docker
make docker-up-build

# View logs
make docker-logs

# Stop services
make docker-down

# Clean everything
make docker-clean
```

### Production Deployment
```bash
# Deploy to staging
make deploy-staging

# Test staging environment
make health-check

# Deploy to production
make deploy-prod
```

## 🔍 Debugging

### Check Environment
```bash
make env-check
```

### View Service Status
```bash
make docker-status
make version
```

### Monitor Logs
```bash
make docker-logs
make docker-logs-backend
make docker-logs-frontend
```

### Test API
```bash
make api-test
make health-check
```

## 🎯 Pro Tips

1. **Use tab completion**: Most terminals support tab completion for Makefile targets
2. **Combine commands**: `make format lint test` runs multiple commands in sequence
3. **Check help first**: `make help` shows all available commands with descriptions
4. **Use environment variables**: Many commands respect environment variables
5. **Git hooks**: `make git-hooks` installs pre-commit hooks for code quality

## 🚨 Common Issues

### Permission Errors
```bash
# Make sure scripts are executable
chmod +x scripts/*
```

### Docker Issues
```bash
# Clean Docker state
make docker-clean

# Restart Docker daemon if needed
```

### Port Conflicts
```bash
# Check what's using ports
make ports
lsof -i :3000
lsof -i :8000
```

### Environment Issues
```bash
# Reset environment
make env-setup

# Check configuration
make env-check
```

## 📚 Advanced Usage

### Custom Database Backup
```bash
# Backup with custom name
make backup-db
# Files saved to backups/backup_YYYYMMDD_HHMMSS.sql
```

### Selective Testing
```bash
# Run only backend tests
make test-backend

# Run with coverage
make test-coverage
```

### Environment-Specific Deployment
```bash
# Deploy to staging
make deploy-staging

# Deploy to production with custom config
make deploy-prod
```

## 🔗 Integration with IDEs

### VS Code
Add to your workspace settings:
```json
{
  "tasks": [
    {
      "type": "shell",
      "command": "make dev",
      "group": "build",
      "label": "Start Development"
    }
  ]
}
```

### IntelliJ/PyCharm
Configure external tools to run Makefile commands.

---

For more information, run `make help` or check the main README.md file.