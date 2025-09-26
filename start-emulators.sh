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

# Wait for services to be ready with simple polling
echo ""
echo "Waiting for services to start (simple polling)..."

# Functions
wait_http() {
  local name="$1"; shift
  local url="$1"; shift
  local max=${3:-60}
  echo "- Waiting for $name at $url"
  for i in $(seq 1 "$max"); do
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
    if [[ "$code" =~ ^2|3 ]]; then
      echo "  $name is ready (HTTP $code)"
      return 0
    fi
    sleep 2
  done
  echo "  ERROR: $name not ready in time"
  return 1
}

wait_tcp() {
  local name="$1"; shift
  local host="$1"; shift
  local port="$1"; shift
  local max=${4:-60}
  echo "- Waiting for $name at $host:$port"
  for i in $(seq 1 "$max"); do
    if (echo > /dev/tcp/$host/$port) >/dev/null 2>&1; then
      echo "  $name is ready"
      return 0
    fi
    sleep 2
  done
  echo "  ERROR: $name not ready in time"
  return 1
}

# Poll key services
wait_http "Firebase UI" "http://localhost:4000"
wait_http "Elasticsearch" "http://localhost:9200/_cluster/health"
wait_http "Qdrant" "http://localhost:6333/healthz"
wait_http "Neo4j HTTP" "http://localhost:7474"
wait_http "A2A Inspector" "http://localhost:8081"

wait_tcp "Spanner gRPC" localhost 9010
wait_tcp "pgAdapter" localhost 5432

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
