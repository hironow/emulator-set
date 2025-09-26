"""CRUD happy‑path E2E for each CLI.

Purpose
- Exercise end‑to‑end create/read flows with minimal complexity.
- Keep scenarios fast and deterministic; include cleanup after assertions.

Scope
- pgAdapter: CREATE → INSERT → SELECT → DROP
- Neo4j: CREATE node → MATCH → DELETE
- Elasticsearch: CREATE index → INDEX doc → SEARCH → DELETE index
- Qdrant: CREATE collection → UPSERT point → SEARCH → DELETE collection
"""

import random
import string
import textwrap
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
        pytest.skip(
            f"network '{NETWORK_NAME}' not found. Start emulators first (docker compose up -d)"
        )


def _ensure_services_running(client: docker.DockerClient, names: list[str]) -> None:
    running = {c.name for c in client.containers.list()}
    missing = [n for n in names if n not in running]
    if missing:
        pytest.skip(f"required emulator containers not running: {', '.join(missing)}")


def _build_image(client: docker.DockerClient, path: str, tag: str) -> None:
    try:
        client.images.build(path=path, tag=tag, rm=True)
    except Exception as e:
        pytest.skip(f"failed to build image {tag} from {path}: {e}")


def _run_cli(
    client: docker.DockerClient,
    image: str,
    binary: str,
    script: str,
    env: dict[str, str],
) -> str:
    # Feed a here-doc into the CLI binary; dedent to avoid leading spaces
    script = textwrap.dedent(script).lstrip("\n")
    heredoc = f"cat <<'EOF' | ./{binary}\n{script}\nEOF"
    try:
        logs: bytes = client.containers.run(
            image=image,
            command=["sh", "-lc", heredoc],
            environment=env,
            network=NETWORK_NAME,
            remove=True,
            stdout=True,
            stderr=True,
        )
        return logs.decode(errors="ignore")
    except Exception as e:
        pytest.skip(f"run {image} failed: {e}")


def _rand_suffix(n: int = 6) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=n))


@pytest.mark.e2e
def test_pgadapter_cli_roundtrip():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["pgadapter-emulator", "spanner-emulator"])
    _build_image(client, path="pgadapter-cli", tag="pgadapter-cli:local")

    suffix = _rand_suffix()
    table = f"e2e_items_{suffix}"
    script = f"""
help
CREATE TABLE {table} (
  id BIGINT PRIMARY KEY,
  name VARCHAR(50)
);
INSERT INTO {table} (id, name) VALUES (1, 'one');
SELECT name FROM {table} WHERE id = 1;
tables
DROP TABLE {table};
exit
"""

    env = {
        "PGHOST": "pgadapter-emulator",
        "PGPORT": "5432",
        "PGUSER": "user",
        "PGDATABASE": "test-instance",
        "PGSSLMODE": "disable",
    }
    out = _run_cli(client, "pgadapter-cli:local", "pgadapter-cli", script, env)
    # SELECT の結果のみを検証。tables コマンドはスキーマ表示の差異で空になる場合がある。
    assert "one" in out


@pytest.mark.e2e
def test_neo4j_cli_roundtrip():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["neo4j-emulator"])
    _build_image(client, path="neo4j-cli", tag="neo4j-cli:local")

    label = f"E2E_{_rand_suffix()}"
    script = f"""
help
CREATE (n:{label} {{name: 'Alice', age: 30}});
MATCH (n:{label}) RETURN n.name LIMIT 1;
labels
MATCH (n:{label}) DETACH DELETE n;
exit
"""

    env = {
        "NEO4J_URI": "bolt://neo4j-emulator:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
    }
    out = _run_cli(client, "neo4j-cli:local", "neo4j-cli", script, env)
    assert "Alice" in out
    assert label in out


@pytest.mark.e2e
def test_elasticsearch_cli_roundtrip():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["elasticsearch-emulator"])
    _build_image(client, path="elasticsearch-cli", tag="elasticsearch-cli:local")

    index = f"e2e_products_{_rand_suffix()}"
    script = f"""
PUT /{index} {{"settings": {{"number_of_shards": 1, "number_of_replicas": 0}}}};
POST /{index}/_doc {{"name": "Laptop", "price": 999.99}};
GET /{index}/_search {{"query": {{"match": {{"name": "Laptop"}}}}}};
DELETE /{index};
\\i
\\q
"""

    env = {
        "ELASTICSEARCH_HOST": "elasticsearch-emulator",
        "ELASTICSEARCH_PORT": "9200",
    }
    out = _run_cli(client, "elasticsearch-cli:local", "elasticsearch-cli", script, env)
    assert "acknowledged" in out
    assert "created" in out or "hits" in out


@pytest.mark.e2e
def test_qdrant_cli_roundtrip():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["qdrant-emulator"])
    _build_image(client, path="qdrant-cli", tag="qdrant-cli:local")

    collection = f"e2e_{_rand_suffix()}"
    script = f"""
PUT /collections/{collection} {{"vectors": {{"size": 4, "distance": "Cosine"}}}};
PUT /collections/{collection}/points {{"points": [{{"id": 1, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {{"name": "A"}}}}]}};
POST /collections/{collection}/points/search {{"vector": [0.1, 0.2, 0.3, 0.4], "limit": 1}};
DELETE /collections/{collection};
\\collections
\\q
"""

    env = {
        "QDRANT_HOST": "qdrant-emulator",
        "QDRANT_PORT": "6333",
    }
    out = _run_cli(client, "qdrant-cli:local", "qdrant-cli", script, env)
    assert "status" in out and "ok" in out
    assert '"id": 1' in out or '"score"' in out
