#!/bin/bash

# Diidemo.hr - Quick Start Script
# This script helps set up and run the entire application with Docker

set -e

echo "🚀 Starting Diidemo.hr Croatian Events Platform..."
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is not available. Please install Docker Compose."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. You can customize it with your own settings."
fi

echo "🏗️  Building and starting all services..."
echo "This may take a few minutes on first run..."
echo ""

# Build and start all services
docker compose up --build -d

echo ""
echo "⏳ Waiting for services to be ready..."

# Wait for services to be healthy
max_attempts=30
attempt=0

while [ $attempt -lt $max_attempts ]; do
    if docker compose ps --format json | jq -e '.[].Health == "healthy" or .[].Health == null' > /dev/null 2>&1; then
        break
    fi
    echo "   Still waiting... (attempt $((attempt + 1))/$max_attempts)"
    sleep 5
    attempt=$((attempt + 1))
done

if [ $attempt -eq $max_attempts ]; then
    echo "⚠️  Services are taking longer than expected to start."
    echo "   You can check the status with: docker compose ps"
    echo "   Or view logs with: docker compose logs"
else
    echo "✅ All services are ready!"
fi

echo ""
echo "🎉 Diidemo.hr is now running!"
echo ""
echo "📱 Access the application:"
echo "   • Frontend:  http://localhost:3000"
echo "   • Backend:   http://localhost:8000"
echo "   • API Docs:  http://localhost:8000/docs"
echo "   • Database:  localhost:5432 (postgres/diidemo2024)"
echo ""
echo "🔧 Useful commands:"
echo "   • Stop:      docker compose down"
echo "   • Logs:      docker compose logs -f"
echo "   • Restart:   docker compose restart"
echo "   • Reset DB:  docker compose down -v && docker compose up --build"
echo ""
echo "📋 The application includes:"
echo "   • 12+ sample Croatian events"
echo "   • Interactive map with event locations"
echo "   • Dark/light theme support"
echo "   • Croatian/English language switching"
echo ""