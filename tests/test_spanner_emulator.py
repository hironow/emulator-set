import pytest
import docker
import time
import socket


def test_spanner_container_starts():
    """Test that the Spanner container starts and is healthy."""
    client = docker.from_env()
    
    # Check if spanner container exists and is running
    try:
        container = client.containers.get('spanner-emulator')
        assert container.status == 'running', f"Spanner container is not running, status: {container.status}"
    except docker.errors.NotFound:
        pytest.fail("Spanner container 'spanner-emulator' not found. Run 'docker compose up spanner-emulator' first.")
    
    # Check if Spanner gRPC endpoint is accessible
    max_retries = 30
    for i in range(max_retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex(('localhost', 9010))
            sock.close()
            if result == 0:
                break
        except Exception:
            pass
        
        if i == max_retries - 1:
            pytest.fail("Spanner gRPC endpoint is not accessible at localhost:9010")
        time.sleep(1)