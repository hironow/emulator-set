import pytest
import docker
import time
import socket


def test_bigtable_container_starts():
    """Test that the Bigtable emulator container starts and is healthy."""
    client = docker.from_env()

    # Check if bigtable container exists and is running
    try:
        container = client.containers.get("bigtable-emulator")
        assert container.status == "running", (
            f"Bigtable container is not running, status: {container.status}"
        )
    except docker.errors.NotFound:
        pytest.fail(
            "Bigtable container 'bigtable-emulator' not found. Run 'docker compose up bigtable-emulator' first."
        )

    # Check if Bigtable gRPC endpoint is accessible
    max_retries = 30
    for i in range(max_retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex(("localhost", 8086))
            sock.close()
            if result == 0:
                break
        except Exception:
            pass

        if i == max_retries - 1:
            pytest.fail("Bigtable gRPC endpoint is not accessible at localhost:8086")
        time.sleep(1)
