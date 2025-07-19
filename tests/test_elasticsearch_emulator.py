import pytest
import docker
import time
import requests


def test_elasticsearch_container_starts():
    """Test that the Elasticsearch container starts and is healthy."""
    client = docker.from_env()

    # Check if elasticsearch container exists and is running
    try:
        container = client.containers.get("elasticsearch-emulator")
        assert container.status == "running", (
            f"Elasticsearch container is not running, status: {container.status}"
        )
    except docker.errors.NotFound:
        pytest.fail(
            "Elasticsearch container 'elasticsearch-emulator' not found. Run 'docker compose up elasticsearch' first."
        )

    # Check if Elasticsearch REST API is accessible
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:9200/_cluster/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            if i == max_retries - 1:
                pytest.fail(
                    "Elasticsearch REST API is not accessible at localhost:9200"
                )
            time.sleep(1)

    # Verify Elasticsearch is ready
    response = requests.get("http://localhost:9200/_cluster/health", timeout=5)
    assert response.status_code == 200, (
        f"Elasticsearch is not ready, status code: {response.status_code}"
    )

    # Check cluster health
    health_data = response.json()
    assert health_data["status"] in ["green", "yellow"], (
        f"Elasticsearch cluster is not healthy: {health_data['status']}"
    )
