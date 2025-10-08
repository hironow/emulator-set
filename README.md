# Emulator Suite

Local, reproducible emulator stack for app development and testing.

Includes Firebase (Auth / Firestore / Storage / Pub/Sub / Eventarc / Tasks),
Spanner (+ pgAdapter), Neo4j, Elasticsearch, Qdrant, and A2A Inspector. Handy
Go-based CLIs and just tasks make day‑to‑day work fast and predictable.

## Table of Contents

- Quick Start
- Services Overview
- Developer Commands
- Testing
- Configuration
- Access
- Data & Persistence
- CLI Tools (details)
- Troubleshooting
- CI

## Quick Start

Start emulators (recommended)

```bash
just start
```

Stop emulators (recommended)

```bash
just stop
```

Or use Docker Compose directly

```bash
docker compose up -d
# ... later
docker compose down
```

## Services Overview

All services run on the `emulator-network`. Defaults are shown; you can change
ports via `.env.local`.

| Service        | Container            | Ports (host → container)                 | Health | CLI |
|----------------|----------------------|------------------------------------------|--------|-----|
| Bigtable       | `bigtable-emulator`  | 8086 → 8086 (gRPC)                       | TCP    | ✓   |
| Firebase UI    | `firebase-emulator`  | 4000 → 4000                              | HTTP   | –   |
| Firestore      | `firebase-emulator`  | 8080 → 8080                              | TCP    | –   |
| Auth           | `firebase-emulator`  | 9099 → 9099                              | TCP    | –   |
| Pub/Sub        | `firebase-emulator`  | 9399 → 9399                              | HTTP   | –   |
| Storage        | `firebase-emulator`  | 9199 → 9199                              | HTTP   | –   |
| Eventarc       | `firebase-emulator`  | 9299 → 9299                              | HTTP   | –   |
| Tasks          | `firebase-emulator`  | 9499 → 9499                              | HTTP   | –   |
| Spanner gRPC   | `spanner-emulator`   | 9010 → 9010                              | TCP    | –   |
| Spanner REST   | `spanner-emulator`   | 9020 → 9020                              | TCP    | –   |
| pgAdapter      | `pgadapter-emulator` | 5432 → 5432 (PostgreSQL)                 | TCP    | ✓   |
| Neo4j          | `neo4j-emulator`     | 7474 → 7474 (HTTP), 7687 → 7687 (Bolt)   | HTTP   | ✓   |
| Elasticsearch  | `elasticsearch-emulator` | 9200 → 9200 (REST), 9300 → 9300     | HTTP   | ✓   |
| Qdrant         | `qdrant-emulator`    | 6333 → 6333 (REST), 6334 → 6334 (gRPC)   | HTTP   | ✓   |
| A2A Inspector  | `a2a-inspector`      | 8081 → 8080                              | HTTP   | –   |
| MLflow         | `mlflow-server`      | 5252 → 5000                              | HTTP   | –   |

> Note: Set `A2A_INSPECTOR_REPO=<git-url>` and/or `A2A_INSPECTOR_REF=<git-ref>` before `just start` to pin the upstream inspector checkout. The image builds via the local `a2a-inspector/Dockerfile`, which fetches the repository and runs on Python 3.12 to satisfy its runtime requirement.

CLI availability (✓) means a matching Go-based REPL is included and runnable
via Docker Compose profiles.

## Developer Commands

Convenience tasks (install just from <https://just.systems>):

- `just test` — Run pytest through `uv run`
- `just gh-validate` — Validate GitHub workflow files using `wrkflw`
- `just gh-run` — Execute a workflow locally (Docker / Podman / Emulation)
- `just gh-tui` — Open `wrkflw` TUI and manage workflows interactively

## Testing

Run all tests

```bash
just test
```

Coverage highlights

- Firestore: Create/Get via REST (runs with emulator-specific permissive rules)
- Auth: SignUp / SignInWithPassword
- Storage: Upload/Download (continues even when the bucket-creation API is unimplemented)
- Pub/Sub: Topic / Subscription / Publish / Pull / Ack via REST
- Eventarc: Port connectivity smoke test
- Spanner / pgAdapter: Container liveness and TCP port checks
- Neo4j / Elasticsearch / Qdrant: Health verification

Test groups

- Smoke: CLI help/info/exit sanity checks
- CRUD: End‑to‑end create/read flows per CLI (with cleanup)
- Features: Aggregations, relationships, filtered vector search
- Negative: pgAdapter/Spanner incompat tests (e.g., missing PK, sequence)

About skipped tests (expected)

- Pub/Sub REST: Some emulator builds or environments may return 500s because of HTTP/2 requirements or unstable REST responses.
  - Tests use aiohttp and skip instead of fail when responses are flaky.
  - On environments where the emulator mandates HTTP/2, the test skips automatically.
- Cloud Tasks REST: Frequently unimplemented; we detect that ahead of time and skip.

Note: Firestore security rules are switched to fully permissive mode for the local emulator to simplify tests. Never use this configuration in production.

## Configuration

All emulators use the same project ID: `test-project`.

Copy example envs and/or export in your shell.

```bash
# Core project configuration
export CLOUDSDK_CORE_PROJECT=test-project
export GOOGLE_CLOUD_PROJECT=test-project
export FIREBASE_PROJECT_ID=test-project

# Firebase Emulator hosts
export FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
export FIRESTORE_EMULATOR_HOST=localhost:8080
export FIREBASE_STORAGE_EMULATOR_HOST=localhost:9199
export PUBSUB_EMULATOR_HOST=localhost:9399

# Spanner Emulator host
export SPANNER_EMULATOR_HOST=localhost:9010
export BIGTABLE_EMULATOR_HOST=localhost:8086

# Authentication (empty for emulators)
export GOOGLE_APPLICATION_CREDENTIALS=""

# Optional
export CLOUD_TASKS_EMULATOR_HOST=localhost:9090
export EVENTARC_EMULATOR=localhost:9299
export JAVA_TOOL_OPTIONS="-Xmx4g"
export CLOUDSDK_SURVEY_DISABLE_PROMPTS=1
```

Docker-to-Docker networking

```bash
export FIREBASE_AUTH_EMULATOR_HOST=firebase:9099
export FIRESTORE_EMULATOR_HOST=firebase:8080
export FIREBASE_STORAGE_EMULATOR_HOST=firebase:9199
export PUBSUB_EMULATOR_HOST=firebase:9399
export SPANNER_EMULATOR_HOST=spanner:9010
export BIGTABLE_EMULATOR_HOST=bigtable-emulator:8086

# MLflow client (inside another container)
export MLFLOW_TRACKING_URI=http://mlflow:5000

**macOS Port Conflicts**
- On macOS, Control Center (AirPlay) commonly binds ports `5000` and `7000`.
- Avoid exposing emulator services on these host ports. This repo uses `5252` for MLflow by default.
```

## Access

- pgAdapter (PostgreSQL): host `localhost`, port `5432`, user `user`, db `test-instance`
- Bigtable: gRPC `localhost:8086`
- Neo4j: Bolt `localhost:7687`, HTTP `localhost:7474` (neo4j / password)
- Elasticsearch: REST `localhost:9200`
- Qdrant: REST `localhost:6333`
- A2A Inspector: `http://localhost:8081`
- MLflow UI: `http://localhost:5252`

Note (A2A Inspector): Entering `localhost` in the web UI resolves inside the container; use `host.docker.internal` to reach the host.

## Data & Persistence

- Firebase data persists under `firebase/data/`.
 - Firebase emulator exports on exit automatically (export-on-exit). `just stop` simply stops containers.
- MLflow experiment data (backend + artifacts) persists under `mlflow-data/`.

## CLI Tools (details)

Docs

- [Firebase Emulator](firebase/README.md)
- [pgAdapter CLI](pgadapter-cli/README.md)
- [Neo4j CLI](neo4j-cli/README.md)
- [Elasticsearch CLI](elasticsearch-cli/README.md)
- [Qdrant CLI](qdrant-cli/README.md)
- [Bigtable CLI](bigtable-cli/README.md)

Run with Docker Compose profiles. Examples:

pgAdapter CLI

```bash
docker compose --profile cli run --rm pgadapter-cli
```

Neo4j CLI

```bash
docker compose --profile cli run --rm neo4j-cli
```

Bigtable CLI

```bash
docker compose --profile cli run --rm bigtable-cli
```

Elasticsearch CLI

```bash
docker compose --profile cli run --rm elasticsearch-cli
```

Qdrant CLI

```bash
docker compose --profile cli run --rm qdrant-cli
```

All CLIs support multi‑line input and print tabular results for readability.

Apple Silicon (arm64)

- Bigtable emulator image is amd64-only; the compose service sets `platform: linux/amd64` to run via emulation.
- Performance impact is usually small for local testing. If you prefer native arm64, consider running the emulator directly on host via `gcloud`.

## Troubleshooting

Health checks

```bash
./check-status.sh
```

Tips

- Firebase UI may take 30–60s to fully start.
- Firestore root endpoint does not return 200; use port listen checks and UI.
- Inspect logs: `docker compose logs -f <service>`
- Test from inside container: `docker compose exec <service> curl ...`
- Verify messages like "ready", "started", or "listening" in logs.

## CI

GitHub Actions workflow `.github/workflows/test-emulators.yaml`:

- Installs dependencies via `uv sync --all-extras --frozen`（lockfile に準拠）
- Runs tests via `uv run pytest`

Use `just gh-validate` locally to sanity‑check workflow files with `wrkflw`.

## pgAdapter / Spanner Dialect Differences

When using pgAdapter (PostgreSQL protocol) on top of Spanner, prefer PostgreSQL
type names and be aware of some limitations. Quick mapping:

| Concept                     | Spanner (GoogleSQL)         | PostgreSQL (via pgAdapter) |
|----------------------------|-----------------------------|-----------------------------|
| Integer                    | `INT64`                     | `BIGINT`                    |
| String (fixed length)      | `STRING(n)`                 | `VARCHAR(n)`                |
| String (unbounded)         | `STRING`                    | `TEXT`                      |
| Floating point             | `FLOAT64`                   | `DOUBLE PRECISION`          |
| Exact decimal              | `NUMERIC`                   | `NUMERIC`                   |
| Timestamp                  | `TIMESTAMP`                 | `TIMESTAMPTZ`               |
| Primary key                | `PRIMARY KEY (id)`          | `id BIGINT PRIMARY KEY` or table-level PK |

Notes

- Every table must have a PRIMARY KEY (Spanner requirement).
- `SERIAL` / `SEQUENCE` are generally unsupported.
- Some PostgreSQL features may be limited compared to stock PostgreSQL.
- Keep DDL simple (explicit PK, basic types) for best compatibility.
# MLflow client (local host)
export MLFLOW_TRACKING_URI=http://localhost:5252
