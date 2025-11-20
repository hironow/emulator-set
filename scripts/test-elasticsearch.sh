#!/usr/bin/env bash
set -euo pipefail

# Test Elasticsearch functionality
# Usage: bash scripts/test-elasticsearch.sh

echo "Testing Elasticsearch..."

# 1. Check cluster health
echo "1. Checking cluster health..."
HEALTH_RESPONSE=$(curl -s http://localhost:9200/_cluster/health)
echo "Response: $HEALTH_RESPONSE"

STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)
echo "Cluster status: $STATUS"

if [[ "$STATUS" != "green" && "$STATUS" != "yellow" ]]; then
  echo "ERROR: Cluster status is not green or yellow" >&2
  exit 1
fi

# 2. Check if shards are initialized
INITIALIZING_SHARDS=$(echo "$HEALTH_RESPONSE" | grep -o '"initializing_shards":[0-9]*' | cut -d':' -f2)
echo "Initializing shards: $INITIALIZING_SHARDS"

if [[ "$INITIALIZING_SHARDS" != "0" ]]; then
  echo "WARNING: Shards are still initializing" >&2
fi

# 3. Create a test index
TEST_INDEX="es_health_check_$(date +%s)"
echo ""
echo "2. Creating test index: $TEST_INDEX"
CREATE_RESPONSE=$(curl -s -X PUT "http://localhost:9200/$TEST_INDEX" \
  -H 'Content-Type: application/json' \
  -d '{
    "settings": {
      "number_of_shards": 1,
      "number_of_replicas": 0
    }
  }')
echo "Response: $CREATE_RESPONSE"

# 4. Wait for index to be ready
echo ""
echo "3. Waiting for index to be ready..."
MAX_WAIT=30
for i in $(seq 1 $MAX_WAIT); do
  INDEX_HEALTH=$(curl -s "http://localhost:9200/_cluster/health/$TEST_INDEX?wait_for_status=yellow&timeout=1s")
  INDEX_STATUS=$(echo "$INDEX_HEALTH" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

  if [[ "$INDEX_STATUS" == "green" || "$INDEX_STATUS" == "yellow" ]]; then
    echo "Index is ready (status: $INDEX_STATUS)"
    break
  fi

  if [[ $i -eq $MAX_WAIT ]]; then
    echo "ERROR: Index not ready after ${MAX_WAIT}s" >&2
    exit 1
  fi

  sleep 1
done

# 5. Insert a test document
echo ""
echo "4. Inserting test document..."
INSERT_RESPONSE=$(curl -s -X POST "http://localhost:9200/$TEST_INDEX/_doc" \
  -H 'Content-Type: application/json' \
  -d '{"test": "document", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}')
echo "Response: $INSERT_RESPONSE"

# 6. Search for the document
echo ""
echo "5. Searching for test document..."
sleep 1  # Wait for indexing
SEARCH_RESPONSE=$(curl -s -X GET "http://localhost:9200/$TEST_INDEX/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "match_all": {}
    }
  }')
echo "Response: $SEARCH_RESPONSE"

HITS=$(echo "$SEARCH_RESPONSE" | grep -o '"total":{"value":[0-9]*' | grep -o '[0-9]*$')
echo "Total hits: $HITS"

if [[ "$HITS" != "1" ]]; then
  echo "ERROR: Expected 1 hit, got $HITS" >&2
  exit 1
fi

# 7. Delete the test index
echo ""
echo "6. Cleaning up test index..."
DELETE_RESPONSE=$(curl -s -X DELETE "http://localhost:9200/$TEST_INDEX")
echo "Response: $DELETE_RESPONSE"

echo ""
echo "✓ All Elasticsearch tests passed!"
