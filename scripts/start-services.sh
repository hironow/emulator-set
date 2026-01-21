#!/usr/bin/env bash
set -euo pipefail

# Start compose services. Idempotent.
# Usage: bash scripts/start-services.sh [--no-build]

NO_BUILD=false
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-build) NO_BUILD=true; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found" >&2
  exit 127
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose not available" >&2
  exit 127
fi

# Create shared network if it doesn't exist (required for telemetry integration)
if ! docker network inspect shared-otel-net >/dev/null 2>&1; then
  echo "Creating shared-otel-net network..."
  docker network create shared-otel-net
fi

if [[ "$NO_BUILD" == true ]]; then
  docker compose up -d --no-build
else
  docker compose up -d
fi

echo "Services started (detached)."

