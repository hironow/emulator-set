#!/usr/bin/env bash
set -euo pipefail

# Run non‑E2E tests.

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install: https://github.com/astral-sh/uv" >&2
  exit 127
fi

echo "Running unit/integration tests (not e2e)"
uv run pytest tests/ -v -m "not e2e"
echo "Done."

