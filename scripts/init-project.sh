#!/bin/bash
# Project initialization script for Diidemo.hr

set -e

echo "🚀 Initializing Diidemo.hr Croatian Events Platform..."
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "Makefile" ]; then
    echo -e "${RED}❌ Please run this script from the project root directory${NC}"
    exit 1
fi

# Welcome message
echo -e "${CYAN}=== Diidemo.hr Project Initialization ===${NC}"
echo ""
echo "This script will help you set up the Croatian Events Platform for development."
echo ""

# Check prerequisites
echo -e "${YELLOW}📋 Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed${NC}"
    echo "Please install Docker Desktop from: https://docker.com/products/docker-desktop"
    exit 1
else
    echo -e "${GREEN}✅ Docker is installed${NC}"
fi

# Check Docker Compose
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not available${NC}"
    echo "Please install Docker Compose"
    exit 1
else
    echo -e "${GREEN}✅ Docker Compose is available${NC}"
fi

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js is not installed (optional for Docker-only setup)${NC}"
else
    echo -e "${GREEN}✅ Node.js is installed: $(node --version)${NC}"
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python is not installed (optional for Docker-only setup)${NC}"
else
    echo -e "${GREEN}✅ Python is installed: $(python3 --version)${NC}"
fi

# Check uv
if ! command -v uv &> /dev/null; then
    echo -e "${YELLOW}⚠️  uv is not installed (optional for Docker-only setup)${NC}"
    echo "Would you like to install uv? (y/n)"
    read -r install_uv
    if [ "$install_uv" = "y" ] || [ "$install_uv" = "Y" ]; then
        echo "Installing uv..."
        curl -LsSf https://astral.sh/uv/install.sh | sh
    fi
else
    echo -e "${GREEN}✅ uv is installed: $(uv --version)${NC}"
fi

echo ""

# Setup environment
echo -e "${YELLOW}🔧 Setting up environment...${NC}"

# Create .env from template if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${GREEN}✅ Created .env file from template${NC}"
else
    echo -e "${BLUE}ℹ️  .env file already exists${NC}"
fi

# Create frontend .env if it doesn't exist
if [ ! -f frontend/.env ] && [ -f frontend/.env.example ]; then
    cp frontend/.env.example frontend/.env
    echo -e "${GREEN}✅ Created frontend/.env file${NC}"
fi

# Create backend .env if it doesn't exist
if [ ! -f backend/.env ] && [ -f backend/.env.example ]; then
    cp backend/.env.example backend/.env
    echo -e "${GREEN}✅ Created backend/.env file${NC}"
fi

echo ""

# Ask about Mapbox token
echo -e "${YELLOW}🗺️  Mapbox Configuration${NC}"
echo "The application uses Mapbox for interactive maps."
echo "You can get a free token at: https://mapbox.com"
echo ""
echo "Do you have a Mapbox access token? (y/n)"
read -r has_mapbox

if [ "$has_mapbox" = "y" ] || [ "$has_mapbox" = "Y" ]; then
    echo "Please enter your Mapbox access token:"
    read -r mapbox_token
    
    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s/VITE_MAPBOX_ACCESS_TOKEN=.*/VITE_MAPBOX_ACCESS_TOKEN=$mapbox_token/" .env
    else
        # Linux
        sed -i "s/VITE_MAPBOX_ACCESS_TOKEN=.*/VITE_MAPBOX_ACCESS_TOKEN=$mapbox_token/" .env
    fi
    echo -e "${GREEN}✅ Mapbox token configured${NC}"
else
    echo -e "${BLUE}ℹ️  You can add a Mapbox token later in the .env file${NC}"
fi

echo ""

# Choose setup method
echo -e "${YELLOW}🚀 Choose setup method:${NC}"
echo "1) Quick Docker setup (recommended)"
echo "2) Full development setup (Docker + local dependencies)"
echo "3) Docker only"
echo ""
echo "Enter your choice (1-3):"
read -r setup_choice

case $setup_choice in
    1)
        echo -e "${GREEN}🐳 Starting Quick Docker setup...${NC}"
        make docker-up-build
        ;;
    2)
        echo -e "${GREEN}🛠️  Starting Full development setup...${NC}"
        make full-setup
        ;;
    3)
        echo -e "${GREEN}🐳 Building Docker images only...${NC}"
        make docker-build
        ;;
    *)
        echo -e "${YELLOW}⚠️  Invalid choice, using Quick Docker setup${NC}"
        make docker-up-build
        ;;
esac

echo ""

# Success message
echo -e "${GREEN}🎉 Diidemo.hr setup completed successfully!${NC}"
echo ""
echo -e "${CYAN}📱 Access your application:${NC}"
echo "  • Frontend:  http://localhost:3000"
echo "  • Backend:   http://localhost:8000"
echo "  • API Docs:  http://localhost:8000/docs"
echo ""
echo -e "${CYAN}🔧 Useful commands:${NC}"
echo "  • make help          - Show all available commands"
echo "  • make dev           - Start development servers"
echo "  • make docker-logs   - View application logs"
echo "  • make health-check  - Check service health"
echo ""
echo -e "${CYAN}📚 Documentation:${NC}"
echo "  • README.md          - Main documentation"
echo "  • MAKEFILE.md        - Makefile command reference"
echo ""
echo "Happy coding! 🚀"