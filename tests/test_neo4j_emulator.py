import pytest
import docker
import asyncio


@pytest.mark.asyncio
async def test_neo4j_container_starts(http_client):
    """Test that the Neo4j container starts and is healthy."""
    client = docker.from_env()

    # Check if neo4j container exists and is running
    try:
        container = client.containers.get("neo4j-emulator")
        assert container.status == "running", (
            f"Neo4j container is not running, status: {container.status}"
        )
    except docker.errors.NotFound:
        pytest.fail(
            "Neo4j container 'neo4j-emulator' not found. Run 'docker compose up neo4j' first."
        )

    # Check if Neo4j HTTP endpoint is accessible
    max_retries = 30
    for i in range(max_retries):
        try:
            async with http_client.get("http://localhost:7474") as response:
                if response.status == 200:
                    break
        except Exception:
            if i == max_retries - 1:
                pytest.fail("Neo4j HTTP endpoint is not accessible at localhost:7474")
            await asyncio.sleep(1)
