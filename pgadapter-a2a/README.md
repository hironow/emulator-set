# pgadapter-a2a

A FastA2A-based server that provides natural language access to PostgreSQL databases using AI.

## Overview

pgadapter-a2a is an AI Agent that allows you to query PostgreSQL databases using natural language. It uses LiteLLM to convert your questions into SQL queries and returns the results.

## Features

- 🤖 Natural language to SQL conversion using LLMs (via LiteLLM)
- 🗄️ PostgreSQL database connection support
- 🚀 FastA2A server for Agent-to-Agent communication
- 💬 Simple CLI interface with Typer

## Usage

### Starting the Server

```bash
# Start with default settings (localhost:8000)
uv run pgadapter-a2a

# Specify host and port
uv run pgadapter-a2a --host 0.0.0.0 --port 3000

# Connect to a specific database
uv run pgadapter-a2a --database-url postgresql://user:password@localhost:5432/mydb

# Or use environment variable
export DATABASE_URL=postgresql://user:password@localhost:5432/mydb
uv run pgadapter-a2a
```

### Configuration

The server uses the following environment variables:

- `DATABASE_URL`: PostgreSQL connection string (default: `postgresql://localhost/postgres`)
- `OPENAI_API_KEY` or other LLM provider keys for LiteLLM

### Example Queries

Once the server is running, you can send natural language queries like:

- "Show me all users"
- "How many orders were placed last month?"
- "List the top 10 customers by revenue"

## Architecture

The system consists of:

1. **DatabaseAgent**: Handles natural language processing and SQL execution
2. **DatabaseAgentSkill**: FastA2A skill wrapper for the agent
3. **FastA2A Server**: Manages Agent-to-Agent communication
4. **CLI**: Typer-based command line interface

## Development

### Running Tests

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_agent.py -v
```

### Project Structure

```txt
pgadapter-a2a/
├── pgadapter_a2a/
│   ├── __init__.py
│   ├── agent.py       # Core AI agent logic
│   ├── skills.py      # FastA2A skill implementation
│   ├── server.py      # FastA2A server setup
│   └── cli.py         # CLI interface
├── tests/             # Test suite
├── pyproject.toml     # Package configuration
└── README.md          # This file
```

## Requirements

- Python 3.13+
- PostgreSQL database
- LLM API key (OpenAI, Anthropic, etc.)

## License

See parent project license.
