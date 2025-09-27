import pytest
import docker
import asyncio


@pytest.mark.asyncio
async def test_elasticsearch_container_starts(http_client):
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
            async with http_client.get(
                "http://localhost:9200/_cluster/health"
            ) as response:
                if response.status == 200:
                    break
        except Exception:
            if i == max_retries - 1:
                pytest.fail(
                    "Elasticsearch REST API is not accessible at localhost:9200"
                )
            await asyncio.sleep(1)

    # Verify Elasticsearch is ready
    async with http_client.get("http://localhost:9200/_cluster/health") as response:
        assert response.status == 200, (
            f"Elasticsearch is not ready, status: {response.status}"
        )
        # Check cluster health
        health_data = await response.json()
    assert health_data["status"] in ["green", "yellow"], (
        f"Elasticsearch cluster is not healthy: {health_data['status']}"
    )
