#!/usr/bin/env bash
set -euo pipefail

# Verify basic PostgreSQL 18 features using psql inside the container.
# - Confirms server version
# - Checks for uuidv7() presence and calls it when available
# - Attempts a virtual generated column; falls back to stored if not supported
# Usage: bash scripts/verify-postgres18.sh

SERVICE=postgres
DB=postgres
USER=postgres

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

echo "🔎 Verifying PostgreSQL 18 features (service: ${SERVICE})"

# Ensure service is running
if ! docker compose ps --quiet "${SERVICE}" | grep -q .; then
  echo "❌ Service '${SERVICE}' is not running. Start with: just up or just start" >&2
  exit 2
fi

psql_exec() {
  local sql="$1"
  docker compose exec -T "${SERVICE}" psql -U "${USER}" -d "${DB}" -Atqc "$sql"
}

# Version check
version=$(psql_exec "show server_version;")
echo "• server_version: ${version}"
major=${version%%.*}
if [[ "$major" == "18" ]]; then
  echo "  ✅ Major version is 18"
else
  echo "  ⚠️  Major version is not 18 (got ${major})"
fi

# uuidv7() presence + sample value
has_uuidv7=$(psql_exec "select exists (select 1 from pg_proc p join pg_namespace n on n.oid=p.pronamespace where p.proname='uuidv7' and n.nspname='pg_catalog');")
if [[ "$has_uuidv7" == "t" ]]; then
  echo "• uuidv7(): present"
  val=$(psql_exec "select uuidv7();") || true
  if [[ -n "${val:-}" ]]; then
    echo "  ✅ uuidv7() sample: ${val}"
  else
    echo "  ⚠️  uuidv7() call did not return a value"
  fi
else
  echo "• uuidv7(): not found"
fi

# Generated column (try virtual, fallback to stored)
echo "• Generated column test"
psql_exec "drop table if exists pg18_gen_test;" >/dev/null || true
if docker compose exec -T "${SERVICE}" psql -U "${USER}" -d "${DB}" -v ON_ERROR_STOP=1 -c "create table pg18_gen_test(x int, y int generated always as (x*2) virtual);" >/dev/null 2>&1; then
  echo "  ✅ Virtual generated column supported"
else
  # Fallback to stored (always supported historically)
  docker compose exec -T "${SERVICE}" psql -U "${USER}" -d "${DB}" -v ON_ERROR_STOP=1 -c "create table pg18_gen_test(x int, y int generated always as (x*2) stored);" >/dev/null
  echo "  ⚠️  Virtual not available; created STORED generated column"
fi
docker compose exec -T "${SERVICE}" psql -U "${USER}" -d "${DB}" -v ON_ERROR_STOP=1 -c "insert into pg18_gen_test(x) values (5);" >/dev/null
pair=$(psql_exec "select x||'->'||y from pg18_gen_test limit 1;")
echo "  ▶︎ sample row: ${pair}"

echo "✅ Verification complete"

