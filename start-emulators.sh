#!/bin/bash

# Start emulators with environment variables

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🚀 Starting emulators..."

# Check if .env.local exists
if [ -f ".env.local" ]; then
    echo -e "${GREEN}✅ Loading environment variables from .env.local${NC}"
    source .env.local
else
    echo -e "${YELLOW}⚠️  No .env.local file found${NC}"
    echo "   Consider creating one from .env.local.example:"
    echo "   cp .env.local.example .env.local"
fi

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo ""
    echo "Please start Docker Desktop:"
    echo "  1. Open Docker Desktop application"
    echo "  2. Wait for Docker to fully start (icon in menu bar)"
    echo "  3. Run this script again"
    echo ""
    
    # Try to detect if Docker Desktop is installed
    if [ -d "/Applications/Docker.app" ]; then
        echo "Docker Desktop appears to be installed."
        echo "You can start it with: open -a Docker"
    else
        echo "Docker Desktop may not be installed."
        echo "Download from: https://www.docker.com/products/docker-desktop"
    fi
    exit 1
fi

# Check ports before starting
echo ""
echo "Checking port availability..."
./check-status.sh | grep -E "(Port|already in use)"

# Check if we're in CI environment
if [ "$CI" = "true" ] || [ "$GITHUB_ACTIONS" = "true" ]; then
    echo "Running in CI environment - non-interactive mode"
    # In CI, always stop existing containers if ports are in use
    if ./check-status.sh | grep -q "already in use"; then
        echo ""
        echo -e "${YELLOW}⚠️  Some ports are already in use - stopping existing containers${NC}"
        docker compose down
        sleep 2
    fi
else
    # Ask user to continue if ports are in use (interactive mode)
    if ./check-status.sh | grep -q "already in use"; then
        echo ""
        echo -e "${YELLOW}⚠️  Some ports are already in use${NC}"
        read -p "Do you want to stop existing containers and continue? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo "Stopping existing containers..."
            docker compose down
            sleep 2
        else
            echo "Exiting..."
            exit 1
        fi
    fi
fi

# Start emulators
echo ""
echo "Starting Docker containers..."
docker compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to start..."
sleep 5

# Follow logs (only in interactive mode)
echo ""
echo -e "${GREEN}✅ Emulators are starting!${NC}"
echo ""

if [ "$CI" = "true" ] || [ "$GITHUB_ACTIONS" = "true" ]; then
    echo "CI environment detected - not following logs"
    echo "Containers are running in background"
    echo ""
    # Show brief status
    docker compose ps
else
    echo "Following logs (press Ctrl+C to stop following)..."
    echo "----------------------------------------"
    docker compose logs -f
fi