# Emulator Suite

This directory contains Docker configurations for running Firebase and Spanner emulators locally.

## Quick Start

### Check Status

Before starting, check if emulators are already running:

```bash
./check-status.sh
```

### Start Emulators

#### Option 1: Using the start script (Recommended)

```bash
./start-emulators.sh
```

This script will:

- Load environment variables from `.env.local` if it exists
- Check port availability
- Start all emulators in detached mode
- Follow the logs automatically

#### Option 2: Using docker compose directly

```bash
docker compose up
```

### Stop Emulators

#### Option 1: Using the stop script (Recommended)

```bash
./stop-emulators.sh
```

This script will:

- Export Firebase data before stopping
- Stop all containers gracefully
- Preserve your data for next session

#### Option 2: Using docker compose directly

```bash
docker compose down
```

If ports are already in use, the start script will prompt you to stop existing emulators.

This will start:

- **Firebase Emulator Suite** with Auth, Firestore, Pub/Sub, Storage, Eventarc, and Tasks
- **Spanner Emulator** with PostgreSQL adapter
- **Neo4j Graph Database** with Bolt and HTTP interfaces
- **A2A Inspector** for debugging Agent-to-Agent protocol implementations

## Ports

### Firebase Emulator

- `4000` - Emulator UI
- `8080` - Firestore
- `9099` - Authentication
- `8085` - Pub/Sub
- `9199` - Storage
- `9299` - Eventarc
- `9499` - Tasks

### Spanner Emulator

- `9010` - gRPC endpoint
- `9020` - REST endpoint
- `5432` - PostgreSQL adapter

### Neo4j

- `7474` - HTTP interface and browser
- `7687` - Bolt protocol

### A2A Inspector

- `8081` - Web interface

### pgAdapter CLI Tool

For interactive database management, use the built-in pgAdapter CLI:

```bash
# Run the CLI tool
docker compose --profile cli run --rm pgadapter-cli
```

#### Features

The pgAdapter CLI is a custom Go-based tool that connects to Spanner Emulator via pgAdapter and provides:

- **Interactive SQL Shell**: Execute SQL queries with a familiar command-line interface
- **Multi-line Support**: Write complex queries across multiple lines (queries execute when you type `;`)
- **Table Formatting**: Query results are displayed in a clean, formatted table with borders
- **Command Shortcuts**:
  - `help` or `\h` - Show available commands and SQL examples
  - `tables` or `\dt` - List all tables in the database
  - `clear` or `\c` - Clear the screen
  - `exit` or `\q` - Exit the CLI
- **Query Timing**: Each query shows execution time
- **PostgreSQL Compatibility**: Works seamlessly with pgAdapter

#### Example Session

```sql
pgadapter> CREATE TABLE users (
      ->   id INT64 NOT NULL,
      ->   name STRING(100),
      ->   email STRING(100)
      -> ) PRIMARY KEY (id);
✅ Query OK, 0 rows affected (125ms)

pgadapter> INSERT INTO users VALUES (1, 'Alice', 'alice@example.com');
✅ Query OK, 1 rows affected (15ms)

pgadapter> SELECT * FROM users;
┌────┬───────┬───────────────────┐
│ ID │ NAME  │ EMAIL             │
├────┼───────┼───────────────────┤
│ 1  │ Alice │ alice@example.com │
└────┴───────┴───────────────────┘
(1 rows) Time: 12ms

pgadapter> tables
📋 Tables (1):
  - users

pgadapter> exit
Goodbye! 👋
```

### Neo4j CLI Tool

For interactive graph database management, use the built-in Neo4j CLI:

```bash
# Run the CLI tool
docker compose --profile cli run --rm neo4j-cli
```

#### Features

The Neo4j CLI is a custom Go-based tool that provides:

- **Interactive Cypher Shell**: Execute Cypher queries with a familiar command-line interface
- **Multi-line Support**: Write complex queries across multiple lines (queries execute when you type `;`)
- **Table Formatting**: Query results displayed in clean, formatted tables
- **Command Shortcuts**:
  - `help` or `\h` - Show available commands and Cypher examples
  - `labels` or `\l` - List all node labels in the database
  - `schema` or `\s` - Show database schema (constraints and indexes)
  - `clear` or `\c` - Clear the screen
  - `exit` or `\q` - Exit the CLI
- **Query Timing**: Each query shows execution time
- **Rich Output**: Node and relationship visualization with properties

#### Example Session

```cypher
neo4j> CREATE (n:Person {name: 'Alice', age: 30});
✅ Query OK: 1 nodes created, 2 properties set, 1 labels added (12ms)

neo4j> CREATE (n:Person {name: 'Bob', age: 25})
    -> CREATE (m:Person {name: 'Charlie', age: 35})
    -> CREATE (n)-[:KNOWS]->(m);
✅ Query OK: 2 nodes created, 4 properties set, 2 labels added, 1 relationships created (8ms)

neo4j> MATCH (n:Person) RETURN n.name, n.age;
┌─────────┬───────┐
│ N.NAME  │ N.AGE │
├─────────┼───────┤
│ Alice   │ 30    │
│ Bob     │ 25    │
│ Charlie │ 35    │
└─────────┴───────┘
(3 rows) Time: 5ms

neo4j> labels
📋 Labels (1):
  - Person

neo4j> exit
Goodbye! 👋
```

### A2A Inspector Access

The A2A Inspector provides a web-based interface for debugging Agent-to-Agent protocol implementations:

- **Web Interface**: http://localhost:8081
- **Features**:
  - Connect to A2A agents
  - View agent cards
  - Perform specification compliance checks
  - Live chat interface
  - Debug console for JSON-RPC 2.0 messages

### Alternative Access Methods

#### Using psql command line

```bash
docker run --rm -it --network emulator-network postgres:15 \
  psql -h pgadapter -U user -d test-instance
```

#### Direct pgAdapter connection

- Host: `localhost`
- Port: `5432`
- Username: `user`
- Password: (empty)
- Database: `test-instance`

#### Direct Neo4j connection

- Host: `localhost`
- Port: `7687` (Bolt) or `7474` (HTTP)
- Username: `neo4j`
- Password: `password`
- Browser UI: http://localhost:7474

## Configuration

All emulators use the same project ID: `test-project`

### Environment Variables

Copy `.env.example` to `.env` to customize ports:

```bash
cp .env.example .env
```

This is useful if default ports are already in use on your system.

## Required Environment Variables

When using the emulators, you need to set the following environment variables in your application to connect to the local services instead of production:

### Core Configuration

```bash
# Project configuration (all emulators use the same project ID)
export CLOUDSDK_CORE_PROJECT=test-project
export GOOGLE_CLOUD_PROJECT=test-project
export FIREBASE_PROJECT_ID=test-project
```

### Emulator Host Configuration

```bash
# Firebase Emulator hosts
export FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
export FIRESTORE_EMULATOR_HOST=localhost:8080
export FIREBASE_STORAGE_EMULATOR_HOST=localhost:9199
export PUBSUB_EMULATOR_HOST=localhost:8085

# Spanner Emulator host
export SPANNER_EMULATOR_HOST=localhost:9010

# Authentication (leave empty for emulators)
export GOOGLE_APPLICATION_CREDENTIALS=""
```

### Optional Environment Variables

```bash
# Cloud Tasks (if using Tasks emulator)
export CLOUD_TASKS_EMULATOR_HOST=localhost:9090

# Eventarc (automatically set by Cloud Functions runtime)
export EVENTARC_EMULATOR=localhost:9299

# JVM memory settings for Java-based emulators
export JAVA_TOOL_OPTIONS="-Xmx4g"

# Disable gcloud SDK telemetry and prompts
export CLOUDSDK_SURVEY_DISABLE_PROMPTS=1
```

### Docker Networking

When running your application in Docker alongside the emulators, use the container names instead of `localhost`:

```bash
# For Docker-to-Docker communication
export FIREBASE_AUTH_EMULATOR_HOST=firebase:9099
export FIRESTORE_EMULATOR_HOST=firebase:8080
export FIREBASE_STORAGE_EMULATOR_HOST=firebase:9199
export PUBSUB_EMULATOR_HOST=firebase:8085
export SPANNER_EMULATOR_HOST=spanner:9010
```

### Development Setup

For local development, you can add these to your shell profile (`.bashrc`, `.zshrc`, etc.) or use a `.env.local` file:

```bash
# .env.local example
CLOUDSDK_CORE_PROJECT=test-project
GOOGLE_CLOUD_PROJECT=test-project
FIREBASE_PROJECT_ID=test-project
FIREBASE_AUTH_EMULATOR_HOST=localhost:9099
FIRESTORE_EMULATOR_HOST=localhost:8080
FIREBASE_STORAGE_EMULATOR_HOST=localhost:9199
PUBSUB_EMULATOR_HOST=localhost:8085
SPANNER_EMULATOR_HOST=localhost:9010
GOOGLE_APPLICATION_CREDENTIALS=
```

### Verifying Configuration

Use the `check-status.sh` script to verify both emulator status and environment variable configuration:

```bash
./check-status.sh
```

The script will:

- Check if emulators are running
- Verify that environment variables are correctly set
- Display warnings for missing or incorrect configurations

### Individual Emulators

If you need to run emulators separately:

```bash
# Firebase only
cd firebase && docker compose up

# Spanner only
cd spanner && docker compose up
```

## Data Persistence

Firebase data is persisted in `firebase/data/` directory. The emulator will automatically import existing data on startup and export on shutdown.

## Troubleshooting

### Health Check Issues

If you see health check warnings even when emulators are running:

1. **Firebase UI not responding**: The Firebase UI may take 30-60 seconds to fully start. Check logs:

   ```bash
   docker compose logs firebase-emulator | grep "All emulators ready"
   ```

2. **Firestore not responding**: Firestore emulator doesn't return HTTP 200 on root endpoint. This is normal behavior. The emulator is working if:
   - Port 8080 is listening (check with `nc -z localhost 8080`)
   - You can access Firestore UI at <http://localhost:4000/firestore>

3. **Connection refused errors**: Ensure Docker is running and ports are not in use:

   ```bash
   # Check if Docker is running
   docker version
   
   # Check port usage
   lsof -i :4000  # Firebase UI
   lsof -i :8080  # Firestore
   ```

### Debugging Tips

1. **Check container logs**:

   ```bash
   # All logs
   docker compose logs
   
   # Follow specific service logs
   docker compose logs -f firebase-emulator
   docker compose logs -f spanner-emulator
   ```

2. **Test from inside container**:

   ```bash
   # Test Firebase UI from inside the container
   docker compose exec firebase-emulator curl http://localhost:4000
   
   # Check running processes
   docker compose exec firebase-emulator ps aux
   ```

3. **Verify emulator readiness**:

   ```bash
   # Look for "All emulators ready!" message
   docker compose logs firebase-emulator | grep -E "(ready|started|listening)"
   ```

4. **Network issues**: If using Docker Desktop, ensure the Docker daemon is running and has proper permissions.
