#!/bin/bash

# Stop emulators gracefully

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "🛑 Stopping emulators..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    echo "No emulators to stop."
    exit 0
fi

# Check if any containers are running
if ! docker compose ps --quiet 2>/dev/null | grep -q .; then
    echo -e "${YELLOW}ℹ️  No emulator containers are running${NC}"
    exit 0
fi

# Show running containers
echo ""
echo "Currently running containers:"
docker compose ps

# Export Firebase data before stopping
echo ""
echo -e "${YELLOW}📤 Exporting Firebase data...${NC}"
docker compose exec -T firebase-emulator firebase emulators:export /firebase/data --force 2>/dev/null || true

# Stop containers
echo ""
echo "Stopping containers..."
docker compose down

echo ""
echo -e "${GREEN}✅ All emulators stopped successfully${NC}"

# Show data persistence info
if [ -d "firebase/data" ] && [ "$(ls -A firebase/data)" ]; then
    echo ""
    echo -e "${GREEN}💾 Firebase data has been persisted in firebase/data/${NC}"
fi