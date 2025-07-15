import pytest
import docker
import time
import requests


def test_qdrant_container_starts():
    """Test that the Qdrant container starts and is healthy."""
    client = docker.from_env()
    
    # Check if qdrant container exists and is running
    try:
        container = client.containers.get('qdrant-emulator')
        assert container.status == 'running', f"Qdrant container is not running, status: {container.status}"
    except docker.errors.NotFound:
        pytest.fail("Qdrant container 'qdrant-emulator' not found. Run 'docker compose up qdrant' first.")
    
    # Check if Qdrant REST API is accessible
    max_retries = 30
    for i in range(max_retries):
        try:
            response = requests.get('http://localhost:6333/healthz', timeout=1)
            if response.status_code == 200:
                break
        except requests.exceptions.RequestException:
            if i == max_retries - 1:
                pytest.fail("Qdrant REST API is not accessible at localhost:6333")
            time.sleep(1)
    
    # Verify Qdrant is ready
    response = requests.get('http://localhost:6333/readyz', timeout=5)
    assert response.status_code == 200, f"Qdrant is not ready, status code: {response.status_code}"