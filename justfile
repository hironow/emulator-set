# https://just.systems

default: help

# List available tasks
help:
    @just --list --unsorted


# Update dependencies with uv
update:
    @echo 'Updating...'
    uv lock --upgrade
    uv sync
    @echo 'Updated.'

# Test pytest
test path='tests/' opts='-v':
    @echo '🧪 Running tests via uv: pytest' '{{path}}' '{{opts}}'
    uv run pytest '{{path}}' '{{opts}}'
    @echo '✅ Tests finished.'

# Fast tests (exclude e2e)
test-fast:
    @bash scripts/run-tests-fast.sh

# E2E tests only
test-e2e:
    @bash scripts/run-tests-e2e.sh

# Pre-build selected images
prebuild images='a2a-inspector firebase-emulator postgres':
    @bash scripts/prebuild-images.sh {{images}}

# Start services (detached)
up nobuild='no':
    @if [ "{{nobuild}}" = 'yes' ]; then \
        bash scripts/start-services.sh --no-build; \
    else \
        bash scripts/start-services.sh; \
    fi

# Wait for services
wait default='60' a2a='180':
    @bash scripts/wait-for-services.sh --default {{default}} --a2a {{a2a}}

# One-shot: prebuild -> up -> wait
start:
    @bash scripts/prebuild-images.sh a2a-inspector firebase-emulator postgres
    @bash scripts/start-services.sh
    @bash scripts/wait-for-services.sh --default 60 --a2a 180

# Stop emulators (with Firebase export)
stop:
    @bash scripts/stop-services.sh

# Show emulator status (containers + endpoints)
check:
    @bash scripts/check-status.sh

# Verify PostgreSQL 18 basics (version, uuidv7 availability)
pg-verify:
    @bash scripts/verify-postgres18.sh

# Check gcloud auth (detailed + strict)
gcloud-auth-check:
    @bash scripts/check-gcloud-auth.sh --details --strict --verbose

# Format
format path='tests/':
    @echo '🔧 Formatting Python with ruff...'
    uv run ruff format '{{path}}'
    @echo '🪄 Formatting Go CLIs with go fmt (if available)...'
    @if command -v go >/dev/null 2>&1; then \
        set -e; \
        for dir in pgadapter-cli neo4j-cli elasticsearch-cli qdrant-cli bigtable-cli postgres-cli; do \
          if [ -f "$dir/go.mod" ]; then \
            echo '  •' "$dir"; \
            (cd "$dir" && go fmt ./...); \
          fi; \
        done; \
        echo '✅ Go formatted.'; \
      else \
        echo '⚠️  go not found; skipping go fmt'; \
      fi
    @echo '✅ Formatting finished.'

# Lint
lint path='tests/' opts='--fix':
    @echo '🔍 Linting code with ruff...'
    uv run ruff check '{{path}}' '{{opts}}'
    @echo 'Semgrep linting...'
    uv run semgrep --config .semgrep/ --error
    @echo '✅ Linting finished.'


# ---- WRKFLW helpers ----

# Validate workflows with wrkflw
[group("wrkflw")]
gh-validate target='':
    @if ! command -v wrkflw >/dev/null 2>&1; then \
        echo '❌ wrkflw not found.'; \
        echo '   Install with: cargo install wrkflw'; \
        exit 127; \
    fi
    @if [ -n "{{target}}" ]; then \
        echo '🔎 Validating workflow:' '{{target}}'; \
        wrkflw validate "{{target}}"; \
    else \
        echo '🔎 Validating workflows in .github/workflows'; \
        wrkflw validate; \
    fi

# Run a workflow locally with wrkflw
[group("wrkflw")]
gh-run file='.github/workflows/test-emulators.yaml' runtime='docker' verbose='true' preserve='':
    @if ! command -v wrkflw >/dev/null 2>&1; then \
        echo '❌ wrkflw not found.'; \
        echo '   Install with: cargo install wrkflw'; \
        exit 127; \
    fi
    @if [ ! -f "{{file}}" ]; then \
        echo '❌ Workflow not found:' '{{file}}'; \
        exit 2; \
    fi
    @set -e; \
    cmd=(wrkflw run "{{file}}"); \
    if [ -n "{{runtime}}" ]; then cmd+=(--runtime "{{runtime}}"); fi; \
    if [ "{{verbose}}" = 'true' ]; then cmd+=(--verbose); fi; \
    if [ "{{preserve}}" = 'true' ]; then cmd+=(--preserve-containers-on-failure); fi; \
    echo '▶️  Running:' "${cmd[@]}"; \
    "${cmd[@]}"

# Check wrkflw availability and show version
[group("wrkflw")]
gh-check:
    @if command -v wrkflw >/dev/null 2>&1; then \
        echo '✅ wrkflw installed:'; wrkflw --version || wrkflw -V || true; \
    else \
        echo '❌ wrkflw not found. Install with: cargo install wrkflw'; \
        exit 127; \
    fi
