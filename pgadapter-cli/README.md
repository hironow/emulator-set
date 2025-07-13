# pgAdapter CLI

A command-line interface for accessing Spanner Emulator through pgAdapter using PostgreSQL protocol.

## Features

- Interactive SQL shell
- Table listing
- Pretty-printed query results
- Query timing
- Multi-line SQL support

## Usage

### Option 1: Run with Go

```bash
go mod download
go run main.go
```

### Option 2: Build and run

```bash
go build -o pgadapter-cli
./pgadapter-cli
```

### Option 3: Run with Docker

```bash
docker build -t pgadapter-cli .
docker run -it --rm --network emulator-network pgadapter-cli
```

## Commands

- `help` or `\h` - Show help
- `tables` or `\dt` - List all tables
- `clear` or `\c` - Clear screen
- `exit` or `\q` - Exit the CLI

## SQL Examples

```sql
-- Create a table
CREATE TABLE users (
  id INT64 NOT NULL,
  name STRING(100),
  email STRING(100),
  created_at TIMESTAMP
) PRIMARY KEY (id);

-- Insert data
INSERT INTO users (id, name, email, created_at)
VALUES (1, 'John Doe', 'john@example.com', CURRENT_TIMESTAMP());

-- Query data
SELECT * FROM users;
```
