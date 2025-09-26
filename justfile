# https://just.systems

default:
    @just --list --unsorted

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

# Format ruff
format path='tests/':
    @echo '🔧 Formatting code with ruff...'
    uv run ruff format '{{path}}'
    @echo '✅ Code formatted.'


# ---- WRKFLW helpers ----

# Validate workflows with wrkflw (target optional)
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

# Run a workflow locally with wrkflw (docker/podman/emulation)
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

# Open wrkflw TUI for workflows (file/dir target optional)
gh-tui target='.github/workflows' runtime='':
    @if ! command -v wrkflw >/dev/null 2>&1; then \
        echo '❌ wrkflw not found.'; \
        echo '   Install with: cargo install wrkflw'; \
        exit 127; \
    fi
    @set -e; \
    cmd=(wrkflw tui "{{target}}"); \
    if [ -n "{{runtime}}" ]; then cmd+=(--runtime "{{runtime}}"); fi; \
    echo '🖥️  TUI:' "${cmd[@]}"; \
    "${cmd[@]}"

# Check wrkflw availability and show version
gh-check:
    @if command -v wrkflw >/dev/null 2>&1; then \
        echo '✅ wrkflw installed:'; wrkflw --version || wrkflw -V || true; \
    else \
        echo '❌ wrkflw not found. Install with: cargo install wrkflw'; \
        exit 127; \
    fi
