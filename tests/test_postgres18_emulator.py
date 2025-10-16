import os
import socket
import time

import docker
import pytest


def test_postgres18_container_starts() -> None:
    client = docker.from_env()

    # Check if postgres container exists and is running
    try:
        container = client.containers.get("postgres-18")
        assert container.status == "running", (
            f"PostgreSQL container is not running, status: {container.status}"
        )
    except docker.errors.NotFound:
        pytest.fail(
            "PostgreSQL container 'postgres-18' not found. Run 'docker compose up postgres' first."
        )

    # Check if PostgreSQL port is accessible
    max_retries = 30
    port = int(os.getenv("POSTGRES_PORT", "5433"))
    for i in range(max_retries):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex(("localhost", port))
            sock.close()
            if result == 0:
                break
        except Exception:
            pass

        if i == max_retries - 1:
            pytest.fail(f"PostgreSQL endpoint is not accessible at localhost:{port}")
        time.sleep(1)
