import pytest
import docker
import asyncio


@pytest.mark.asyncio
async def test_qdrant_container_starts(http_client):
    """Test that the Qdrant container starts and is healthy."""
    client = docker.from_env()

    # Check if qdrant container exists and is running
    try:
        container = client.containers.get("qdrant-emulator")
        assert container.status == "running", (
            f"Qdrant container is not running, status: {container.status}"
        )
    except docker.errors.NotFound:
        pytest.fail(
            "Qdrant container 'qdrant-emulator' not found. Run 'docker compose up qdrant' first."
        )

    # Check if Qdrant REST API is accessible
    max_retries = 30
    for i in range(max_retries):
        try:
            async with http_client.get("http://localhost:6333/healthz") as response:
                if response.status == 200:
                    break
        except Exception:
            if i == max_retries - 1:
                pytest.fail("Qdrant REST API is not accessible at localhost:6333")
            await asyncio.sleep(1)

    # Verify Qdrant is ready
    async with http_client.get("http://localhost:6333/readyz") as response:
        assert response.status == 200, f"Qdrant is not ready, status: {response.status}"
