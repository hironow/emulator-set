import pytest
import docker
import time
import requests


def test_firebase_container_starts():
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
            response = requests.get("http://localhost:4000", timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            if i == max_retries - 1:
                pytest.fail("Firebase UI is not accessible at localhost:4000")
            time.sleep(1)
