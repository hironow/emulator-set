#!/usr/bin/env bash
set -euo pipefail

# Run E2E tests and tee to e2e.log

if ! command -v uv >/dev/null 2>&1; then
  echo "uv not found. Install: https://github.com/astral-sh/uv" >&2
  exit 127
fi

echo "Running E2E tests"
uv run pytest tests/e2e -v -m e2e -ra
echo "Done."

