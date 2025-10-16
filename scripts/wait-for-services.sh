#!/usr/bin/env bash
set -euo pipefail

# Idempotent waiter for emulator services.
# Usage: bash scripts/wait-for-services.sh [--default <sec>] [--a2a <sec>]

DEFAULT_WAIT=60
A2A_WAIT=180

while [[ $# -gt 0 ]]; do
  case "$1" in
    --default)
      DEFAULT_WAIT="${2:-60}"; shift 2 ;;
    --a2a)
      A2A_WAIT="${2:-180}"; shift 2 ;;
    *)
      echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

echo "Waiting for emulator services..."

wait_http() {
  local name="$1"; shift
  local url="$1"; shift
  local max="${1:-$DEFAULT_WAIT}"
  echo "- Waiting for ${name} at ${url}"
  for i in $(seq 1 "$max"); do
    local code
    code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
    if [[ "$code" =~ ^2|3 ]]; then
      echo "  ${name} is ready (HTTP ${code})"
      return 0
    fi
    sleep 2
  done
  echo "  ERROR: ${name} not ready in time" >&2
  return 1
}

wait_tcp() {
  local name="$1"; shift
  local host="$1"; shift
  local port="$1"; shift
  local max="${1:-$DEFAULT_WAIT}"
  echo "- Waiting for ${name} at ${host}:${port}"
  for i in $(seq 1 "$max"); do
    if (echo > /dev/tcp/${host}/${port}) >/dev/null 2>&1; then
      echo "  ${name} is ready"
      return 0
    fi
    sleep 2
  done
  echo "  ERROR: ${name} not ready in time" >&2
  return 1
}

wait_http "Firebase UI" "http://localhost:4000" "$DEFAULT_WAIT"
wait_http "Elasticsearch" "http://localhost:9200/_cluster/health" "$DEFAULT_WAIT"
wait_http "Qdrant" "http://localhost:6333/healthz" "$DEFAULT_WAIT"
wait_http "Neo4j HTTP" "http://localhost:7474" "$DEFAULT_WAIT"
wait_http "A2A Inspector" "http://localhost:8081" "$A2A_WAIT"
wait_http "MLflow" "http://localhost:5252/" "$DEFAULT_WAIT"

wait_tcp "Spanner gRPC" localhost 9010 "$DEFAULT_WAIT"
wait_tcp "pgAdapter" localhost "${PGADAPTER_PORT:-55432}" "$DEFAULT_WAIT"
wait_tcp "Bigtable Emulator" localhost 8086 "$DEFAULT_WAIT"
wait_tcp "PostgreSQL 18" localhost "${POSTGRES_PORT:-5433}" "$DEFAULT_WAIT"

echo "All targeted services reported ready."
