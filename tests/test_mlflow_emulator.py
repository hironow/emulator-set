import pytest
import docker
import asyncio


@pytest.mark.asyncio
async def test_mlflow_container_starts(http_client):
    """MLflow container should be running and UI reachable."""
    client = docker.from_env()

    # Check if mlflow container exists and is running
    try:
        container = client.containers.get("mlflow-server")
        assert container.status == "running", (
            f"MLflow container is not running, status: {container.status}"
        )
    except docker.errors.NotFound:
        pytest.fail(
            "MLflow container 'mlflow-server' not found. Run 'docker compose up mlflow' first."
        )

    # Check if MLflow UI is accessible
    import os
    port = os.environ.get("MLFLOW_PORT", "5252")
    base = f"http://localhost:{port}/"
    max_retries = 30
    for i in range(max_retries):
        try:
            async with http_client.get(base) as response:
                if response.status in (200, 302):
                    break
        except Exception:
            if i == max_retries - 1:
                pytest.fail(f"MLflow UI is not accessible at {base}")
            await asyncio.sleep(1)

    # Final verification
    async with http_client.get(base) as response:
        assert response.status in (200, 302), (
            f"MLflow UI not ready, status: {response.status}"
        )
