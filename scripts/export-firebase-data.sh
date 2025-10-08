#!/usr/bin/env bash
set -euo pipefail

# Export Firebase emulator data if the service is running.
# Usage: bash scripts/export-firebase-data.sh [service] [export_path]
#   service: docker-compose service/container name (default: firebase-emulator)
#   export_path: path inside container (default: /firebase/data)

SERVICE="${1:-firebase-emulator}"
EXPORT_PATH="${2:-/firebase/data}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found; skipping firebase export" >&2
  exit 0
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose not available; skipping firebase export" >&2
  exit 0
fi

# Only attempt export if container is running
if docker ps --format '{{.Names}}' | grep -q "^${SERVICE}$"; then
  echo "📤 Exporting Firebase data from ${SERVICE} to ${EXPORT_PATH} ..."
  # firebase CLI is bundled in the emulator image
  if docker compose exec -T "${SERVICE}" firebase emulators:export "${EXPORT_PATH}" --force 2>/dev/null; then
    echo "✅ Firebase data export completed."
  else
    echo "⚠️  Firebase data export failed or not supported; continuing."
  fi
else
  echo "ℹ️  ${SERVICE} is not running; skipping export."
fi

