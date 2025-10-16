#!/usr/bin/env bash
set -euo pipefail

# Show the current status of emulator containers and their host endpoints.
# Idempotent, read-only.
# Usage: bash scripts/check-status.sh

# Move to repo root (script lives in scripts/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${SCRIPT_DIR}/.."

need() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "❌ Required command not found: $1" >&2
    exit 127
  fi
}

need docker

if ! docker compose version >/dev/null 2>&1; then
  echo "❌ docker compose not available" >&2
  exit 127
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "❌ curl not found (needed for HTTP checks)" >&2
  exit 127
fi

container_status() {
  local name="$1"
  # Print container status line if exists, else "not found"
  local out
  out=$(docker ps -a --filter name="^/${name}$" --format '{{.Status}}' || true)
  if [[ -z "$out" ]]; then
    echo "not found"
  else
    echo "$out"
  fi
}

check_http() {
  local url="$1"
  local code
  code=$(curl -s -o /dev/null -w "%{http_code}" "$url" || true)
  if [[ "$code" =~ ^2|3 ]]; then
    echo "✅ HTTP ${code}"
  elif [[ "$code" == "000" ]]; then
    echo "❌ no response"
  else
    echo "⚠️  HTTP ${code}"
  fi
}

check_tcp() {
  local host="$1"; shift
  local port="$1"; shift
  if command -v nc >/dev/null 2>&1; then
    if nc -z "$host" "$port" >/dev/null 2>&1; then
      echo "✅ open"
    else
      echo "❌ closed"
    fi
  else
    # Fallback: bash /dev/tcp
    if (echo > /dev/tcp/${host}/${port}) >/dev/null 2>&1; then
      echo "✅ open"
    else
      echo "❌ closed"
    fi
  fi
}

report() {
  local label="$1"; shift
  local container="$1"; shift
  local mode="$1"; shift
  local target="$1"; shift

  # Container status
  local cstat
  cstat=$(container_status "$container")

  # Endpoint check
  local estat
  if [[ "$mode" == http ]]; then
    estat=$(check_http "$target")
  else
    local host port
    host="${target%:*}"; port="${target#*:}"
    estat=$(check_tcp "$host" "$port")
  fi

  printf "%-18s | %-28s | %s\n" "$label" "$cstat" "$estat"
}

echo "📦 Docker Compose services"
docker compose ps || true
echo
echo "🔎 Emulator endpoints"
printf "%-18s | %-28s | %s\n" "Service" "Container status" "Endpoint check"
printf "%s\n" "------------------+------------------------------+-------------------------"

# Firebase (UI)
report "Firebase UI"       firebase-emulator      http  "http://localhost:4000"

# Bigtable
report "Bigtable gRPC"     bigtable-emulator      tcp   "localhost:8086"

# Spanner / pgAdapter
report "Spanner gRPC"      spanner-emulator       tcp   "localhost:9010"
report "pgAdapter"         pgadapter-emulator     tcp   "localhost:${PGADAPTER_PORT:-55432}"

# Neo4j
report "Neo4j HTTP"        neo4j-emulator         http  "http://localhost:7474"

# Elasticsearch
report "Elasticsearch"     elasticsearch-emulator http  "http://localhost:9200/_cluster/health"

# Qdrant
report "Qdrant"            qdrant-emulator        http  "http://localhost:6333/healthz"

# A2A Inspector
report "A2A Inspector"     a2a-inspector          http  "http://localhost:8081"

# MLflow
report "MLflow"            mlflow-server          http  "http://localhost:5252/"

# PostgreSQL (pure)
report "PostgreSQL 18"     postgres-18            tcp   "localhost:${POSTGRES_PORT:-5433}"

echo
echo "Done."
