import pytest
import docker
import time
import httpx


def test_a2a_inspector_container_starts():
    """Test that the A2A Inspector container starts and is healthy."""
    client = docker.from_env()

    # Check if a2a-inspector container exists and is running
    try:
        container = client.containers.get("a2a-inspector")
        assert container.status == "running", (
            f"A2A Inspector container is not running, status: {container.status}"
        )
    except docker.errors.NotFound:
        pytest.fail(
            "A2A Inspector container 'a2a-inspector' not found. Run 'docker compose up a2a-inspector' first."
        )

    # Check if A2A Inspector HTTP endpoint is accessible
    max_retries = 30
    for i in range(max_retries):
        try:
            response = httpx.get("http://localhost:8081", timeout=1)
            if response.status_code == 200:
                break
        except httpx.HTTPError:
            if i == max_retries - 1:
                pytest.fail(
                    "A2A Inspector HTTP endpoint is not accessible at localhost:8081"
                )
            time.sleep(1)
