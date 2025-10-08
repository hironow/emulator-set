#!/usr/bin/env bash
set -euo pipefail

# Stop emulator services gracefully.
# Usage: bash scripts/stop-services.sh [--no-export]

DO_EXPORT=1
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-export) DO_EXPORT=0; shift ;;
    *) echo "Unknown arg: $1" >&2; exit 2 ;;
  esac
done

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found. Nothing to stop." >&2
  exit 0
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose not available. Nothing to stop." >&2
  exit 0
fi

# Show running containers (if any)
if docker compose ps --quiet 2>/dev/null | grep -q .; then
  echo "📦 Currently running containers:"
  docker compose ps
else
  echo "ℹ️  No emulator containers are running"
  exit 0
fi

# Export Firebase data unless disabled
if [[ "$DO_EXPORT" -eq 1 ]]; then
  bash "$(dirname "$0")/export-firebase-data.sh" firebase-emulator /firebase/data || true
fi

echo "🛑 Stopping containers..."
docker compose down
echo "✅ All emulators stopped."

