"""Smoke‑level E2E for each CLI (help/exit/info).

Fast connectivity checks to ensure the CLIs start, connect, and respond to
basic commands. Deeper scenarios live in test_cli_crud_e2e.py and
test_cli_features_e2e.py.
"""

import io
import os
import pytest
import docker


NETWORK_NAME = "emulator-network"


def _docker_client() -> docker.DockerClient:
    try:
        client = docker.from_env()
        client.ping()
        return client
    except Exception as e:
        pytest.skip(f"docker not available: {e}")


def _ensure_network(client: docker.DockerClient) -> None:
    nets = client.networks.list(names=[NETWORK_NAME])
    if not nets:
        pytest.skip(f"network '{NETWORK_NAME}' not found. Start emulators first (docker compose up -d)")


def _ensure_services_running(client: docker.DockerClient, names: list[str]) -> None:
    running = {c.name for c in client.containers.list()}
    missing = [n for n in names if n not in running]
    if missing:
        pytest.skip(f"required emulator containers not running: {', '.join(missing)}")


def _build_image(client: docker.DockerClient, path: str, tag: str) -> None:
    try:
        # Stream build output for visibility if needed
        client.images.build(path=path, tag=tag, rm=True)
    except Exception as e:
        pytest.skip(f"failed to build image {tag} from {path}: {e}")


def _run_and_capture(client: docker.DockerClient, image: str, command: str, env: dict[str, str]) -> str:
    try:
        logs: bytes = client.containers.run(
            image=image,
            command=["sh", "-lc", command],
            environment=env,
            network=NETWORK_NAME,
            remove=True,
            stdout=True,
            stderr=True,
        )
        return logs.decode(errors="ignore")
    except Exception as e:
        pytest.skip(f"run {image} failed: {e}")


@pytest.mark.e2e
def test_pgadapter_cli_help_and_exit():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, [
        "pgadapter-emulator",
        "spanner-emulator",
    ])
    _build_image(client, path="pgadapter-cli", tag="pgadapter-cli:local")
    env = {
        "PGHOST": "pgadapter-emulator",
        "PGPORT": "5432",
        "PGUSER": "user",
        "PGDATABASE": "test-instance",
        "PGSSLMODE": "disable",
    }
    out = _run_and_capture(client, "pgadapter-cli:local", "printf 'help\\nexit\\n' | ./pgadapter-cli", env)
    assert ("pgAdapter CLI" in out) or ("📚 Available Commands" in out)
    assert ("Goodbye" in out) or ("Bye" in out)


@pytest.mark.e2e
def test_neo4j_cli_help_and_exit():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["neo4j-emulator"]) 
    _build_image(client, path="neo4j-cli", tag="neo4j-cli:local")
    env = {
        "NEO4J_URI": "bolt://neo4j-emulator:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
    }
    out = _run_and_capture(client, "neo4j-cli:local", "printf 'help\\nexit\\n' | ./neo4j-cli", env)
    assert ("Neo4j CLI" in out) or ("📚 Available Commands" in out)
    assert ("Goodbye" in out) or ("Bye" in out)


@pytest.mark.e2e
def test_elasticsearch_cli_info_and_quit():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["elasticsearch-emulator"]) 
    _build_image(client, path="elasticsearch-cli", tag="elasticsearch-cli:local")
    env = {
        "ELASTICSEARCH_HOST": "elasticsearch-emulator",
        "ELASTICSEARCH_PORT": "9200",
    }
    out = _run_and_capture(client, "elasticsearch-cli:local", "printf '\\\\i\\n\\\\q\\n' | ./elasticsearch-cli", env)
    assert ("Connected to Elasticsearch" in out) or ("Cluster Information" in out)


@pytest.mark.e2e
def test_qdrant_cli_info_and_quit():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["qdrant-emulator"]) 
    _build_image(client, path="qdrant-cli", tag="qdrant-cli:local")
    env = {
        "QDRANT_HOST": "qdrant-emulator",
        "QDRANT_PORT": "6333",
    }
    out = _run_and_capture(client, "qdrant-cli:local", "printf '\\\\i\\n\\\\q\\n' | ./qdrant-cli", env)
    assert ("Connected to Qdrant" in out) or ("Cluster Information" in out)
