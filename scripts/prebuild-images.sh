#!/usr/bin/env bash
set -euo pipefail

# Pre-build selected compose images to speed up startup and CI waits.
# Usage: bash scripts/prebuild-images.sh [services...]

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found" >&2
  exit 127
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose not available" >&2
  exit 127
fi

services=("a2a-inspector" "firebase-emulator")
if [[ $# -gt 0 ]]; then
  services=("$@")
fi

echo "Pre-building images: ${services[*]}"

# Build each service, allowing per-service platform overrides where needed
for svc in "${services[@]}"; do
  echo "▶️  Building $svc"
  docker compose build "$svc"
done
echo "Done."
