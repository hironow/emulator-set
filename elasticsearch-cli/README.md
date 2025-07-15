# Elasticsearch CLI

A command-line interface for interacting with Elasticsearch.

## Usage

The CLI is configured through environment variables:
- `ELASTICSEARCH_HOST`: Elasticsearch host (default: localhost)
- `ELASTICSEARCH_PORT`: Elasticsearch port (default: 9200)

## Commands

### Special Commands
- `\h` or `\help` - Show help message
- `\q` or `\quit` - Exit the CLI
- `\c` or `\clear` - Clear the screen
- `\l` or `\indices` - List all indices
- `\i` or `\info` - Show cluster info
- `\health` - Show cluster health

### API Commands
All API commands must end with a semicolon (`;`).

Examples:
```
GET /_cat/indices;
PUT /test_index {"settings": {"number_of_shards": 1}};
POST /test_index/_doc {"title": "Test Document"};
GET /test_index/_search {"query": {"match_all": {}}};
DELETE /test_index;
```