import pytest
import docker
import asyncio


@pytest.mark.asyncio
async def test_firebase_container_starts(http_client):
    """Test that the Firebase container starts and is healthy."""
    client = docker.from_env()

    # Check if firebase container exists and is running
    try:
        container = client.containers.get("firebase-emulator")
        assert container.status == "running", (
            f"Firebase container is not running, status: {container.status}"
        )
    except docker.errors.NotFound:
        pytest.fail(
            "Firebase container 'firebase-emulator' not found. Run 'docker compose up firebase-emulator' first."
        )

    # Check if Firebase UI is accessible
    max_retries = 30
    for i in range(max_retries):
        try:
            async with http_client.get("http://localhost:4000") as response:
                if response.status == 200:
                    break
        except Exception:
            if i == max_retries - 1:
                pytest.fail("Firebase UI is not accessible at localhost:4000")
            await asyncio.sleep(1)
