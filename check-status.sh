#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 Checking emulator status..."
echo ""

# Check Docker status first
echo "Docker Status:"
if docker info > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Docker daemon is running${NC}"
    docker_version=$(docker version --format '{{.Server.Version}}' 2>/dev/null || echo "unknown")
    echo -e "   Version: ${docker_version}"
else
    echo -e "${RED}❌ Docker daemon is not running${NC}"
    if [ -d "/Applications/Docker.app" ]; then
        echo -e "${YELLOW}   Docker Desktop is installed. Start it with: open -a Docker${NC}"
    else
        echo -e "${YELLOW}   Docker Desktop may not be installed${NC}"
    fi
fi
echo ""

# Check if emulator containers are running
is_emulator_running() {
    docker ps --format "{{.Names}}" 2>/dev/null | grep -E "(firebase-emulator|spanner-emulator|pgadapter)" > /dev/null 2>&1
}

# Check if any ports are in use
check_port() {
    local port=$1
    local service=$2
    local container_name=$3
    
    if lsof -i :$port > /dev/null 2>&1; then
        # Port is in use - check if it's by our emulator
        if is_emulator_running && [ -n "$container_name" ] && docker ps --format "{{.Names}}" | grep -q "$container_name"; then
            echo -e "${GREEN}✅ Port $port ($service) is in use by emulator${NC}"
            return 0
        else
            echo -e "${RED}❌ Port $port ($service) is already in use${NC}"
            lsof -i :$port | grep LISTEN | head -1
            return 1
        fi
    else
        echo -e "${GREEN}✅ Port $port ($service) is available${NC}"
        return 0
    fi
}

# Firebase ports
echo "Firebase Emulator Ports:"
check_port 4000 "Firebase UI" "firebase-emulator"
check_port 8080 "Firestore" "firebase-emulator"
check_port 9099 "Auth" "firebase-emulator"
check_port 8085 "Pub/Sub" "firebase-emulator"
check_port 9199 "Storage" "firebase-emulator"
check_port 9299 "Eventarc" "firebase-emulator"
check_port 9499 "Tasks" "firebase-emulator"

echo ""

# Spanner ports
echo "Spanner Emulator Ports:"
check_port 9010 "Spanner gRPC" "spanner-emulator"
check_port 9020 "Spanner REST" "spanner-emulator"
check_port 5432 "PostgreSQL Adapter" "pgadapter"

echo ""

# Check Docker containers
echo "Docker Containers:"
if is_emulator_running; then
    echo -e "${GREEN}📦 Emulator containers are running:${NC}"
    docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "(firebase-emulator|spanner-emulator|pgadapter|NAMES)"
    EMULATORS_RUNNING=true
else
    echo -e "${YELLOW}ℹ️  No emulator containers are running${NC}"
    EMULATORS_RUNNING=false
fi

echo ""

# Health check endpoints
echo "Health Check Endpoints:"

# Function to check if port is listening
check_service_port() {
    local port=$1
    local service=$2
    
    if nc -z localhost $port 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# Check if any containers are running first
if docker ps 2>/dev/null | grep -E "(firebase-emulator|spanner-emulator|pgadapter)" > /dev/null 2>&1; then
    # Firebase UI health check (check if port is listening)
    if check_service_port 4000 "Firebase UI"; then
        # Try to fetch the page content
        http_code=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:4000 2>/dev/null)
        if [ "$http_code" = "200" ]; then
            echo -e "${GREEN}✅ Firebase UI is running and accessible (http://localhost:4000)${NC}"
        else
            echo -e "${GREEN}✅ Firebase UI is running on port 4000${NC} (HTTP $http_code)"
        fi
    else
        echo -e "${YELLOW}⚠️  Firebase UI port 4000 is not listening${NC}"
    fi

    # Firestore health check (check if port is listening)
    if check_service_port 8080 "Firestore"; then
        # Firestore doesn't return 200 on root, but we can check if it's accepting connections
        echo -e "${GREEN}✅ Firestore is running on port 8080${NC}"
    else
        echo -e "${YELLOW}⚠️  Firestore port 8080 is not listening${NC}"
    fi
    
    # Additional service checks
    if check_service_port 9099 "Auth"; then
        echo -e "${GREEN}✅ Authentication service is running on port 9099${NC}"
    fi
    
    if check_service_port 5432 "PostgreSQL/pgAdapter"; then
        echo -e "${GREEN}✅ pgAdapter is running on port 5432${NC}"
    fi
else
    echo -e "${YELLOW}ℹ️  No emulator containers detected - health checks skipped${NC}"
    echo -e "${YELLOW}    Run 'docker compose up' to start the emulators${NC}"
fi

echo ""

# Environment variable checks
echo "Environment Variable Configuration:"
echo ""

# Function to check environment variable
check_env_var() {
    local var_name=$1
    local expected_value=$2
    local description=$3
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        echo -e "${RED}❌ $var_name is not set${NC} - $description"
        return 1
    elif [ -n "$expected_value" ] && [ "$var_value" != "$expected_value" ]; then
        echo -e "${YELLOW}⚠️  $var_name=$var_value${NC} (expected: $expected_value) - $description"
        return 1
    else
        echo -e "${GREEN}✅ $var_name=$var_value${NC}"
        return 0
    fi
}

# Check core project configuration
echo "Core Project Configuration:"
check_env_var "CLOUDSDK_CORE_PROJECT" "test-project" "Google Cloud SDK project"
check_env_var "GOOGLE_CLOUD_PROJECT" "test-project" "Google Cloud libraries project"
check_env_var "FIREBASE_PROJECT_ID" "test-project" "Firebase project ID"

echo ""

# Check emulator hosts
echo "Emulator Host Configuration:"
check_env_var "FIREBASE_AUTH_EMULATOR_HOST" "" "Firebase Auth emulator (e.g., localhost:9099)"
check_env_var "FIRESTORE_EMULATOR_HOST" "" "Firestore emulator (e.g., localhost:8080)"
check_env_var "FIREBASE_STORAGE_EMULATOR_HOST" "" "Firebase Storage emulator (e.g., localhost:9199)"
check_env_var "PUBSUB_EMULATOR_HOST" "" "Pub/Sub emulator (e.g., localhost:8085)"
check_env_var "SPANNER_EMULATOR_HOST" "" "Spanner emulator (e.g., localhost:9010)"

echo ""

# Check authentication
echo "Authentication Configuration:"
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo -e "${YELLOW}⚠️  GOOGLE_APPLICATION_CREDENTIALS is set${NC} - Should be empty for emulators"
else
    echo -e "${GREEN}✅ GOOGLE_APPLICATION_CREDENTIALS is empty${NC} - Correct for emulators"
fi

echo ""

# Summary and recommendations
echo "Summary:"

# Check overall status
if [ "$EMULATORS_RUNNING" = true ]; then
    echo -e "${GREEN}✅ Emulators are running${NC}"
    echo ""
    echo "Access points:"
    echo "  - Firebase UI: http://localhost:4000"
    echo "  - Firestore: localhost:8080"
    echo "  - Auth: localhost:9099"
    echo "  - pgAdapter: localhost:5432"
elif [ -z "$FIRESTORE_EMULATOR_HOST" ] && [ -z "$FIREBASE_AUTH_EMULATOR_HOST" ] && [ -z "$SPANNER_EMULATOR_HOST" ]; then
    echo -e "${YELLOW}⚠️  No emulator host variables are set${NC}"
    echo ""
    echo "To connect to the emulators, set these environment variables:"
    echo ""
    echo "  export CLOUDSDK_CORE_PROJECT=test-project"
    echo "  export GOOGLE_CLOUD_PROJECT=test-project"
    echo "  export FIREBASE_PROJECT_ID=test-project"
    echo "  export FIREBASE_AUTH_EMULATOR_HOST=localhost:9099"
    echo "  export FIRESTORE_EMULATOR_HOST=localhost:8080"
    echo "  export FIREBASE_STORAGE_EMULATOR_HOST=localhost:9199"
    echo "  export PUBSUB_EMULATOR_HOST=localhost:8085"
    echo "  export SPANNER_EMULATOR_HOST=localhost:9010"
    echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"\""
    echo ""
    echo "Or add them to your .env.local file."
else
    echo -e "${GREEN}✅ Emulator environment variables are configured${NC}"
fi

echo ""
echo "💡 Tips:"
echo "  - Run 'docker compose down' to stop all emulators"
echo "  - Run 'docker compose up' to start all emulators"
echo "  - Run 'source .env.local' to load environment variables from file"
echo "  - Use 'docker compose logs' to view emulator logs"
echo "  - Use 'docker compose logs -f firebase-emulator' to follow Firebase logs"
echo "  - Use 'docker compose exec firebase-emulator curl http://localhost:4000' to test from inside container"