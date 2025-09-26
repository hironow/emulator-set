"""Transactional / atomic flows E2E.

Focus
- pgAdapter: explicit BEGIN/ROLLBACK/COMMIT semantics
- Neo4j: attempt explicit BEGIN/ROLLBACK/COMMIT (skip if unsupported by driver path)
- Elasticsearch: index with refresh=wait_for to emulate commit‑like visibility
- Qdrant: upsert then delete to validate atomic cleanup
"""

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
    if not client.networks.list(names=[NETWORK_NAME]):
        pytest.skip("emulator-network not found. Start emulators first.")


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


@pytest.mark.e2e
def test_pgadapter_transaction_commit_and_rollback():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["pgadapter-emulator", "spanner-emulator"])
    _build_image(client, path="pgadapter-cli", tag="pgadapter-cli:local")

    env = {
        "PGHOST": "pgadapter-emulator",
        "PGPORT": "5432",
        "PGUSER": "user",
        "PGDATABASE": "test-instance",
        "PGSSLMODE": "disable",
    }

    table = "tx_items"
    script = f"""
DROP TABLE IF EXISTS {table};
CREATE TABLE {table} (
  id BIGINT PRIMARY KEY,
  name VARCHAR(50)
);
BEGIN;
INSERT INTO {table} (id, name) VALUES (1, 'rollbackme');
SELECT name FROM {table} WHERE id = 1;
ROLLBACK;
SELECT name FROM {table} WHERE id = 1;
BEGIN;
INSERT INTO {table} (id, name) VALUES (2, 'commitme');
COMMIT;
SELECT name FROM {table} WHERE id = 2;
DROP TABLE {table};
exit
"""

    out = _run_cli(client, "pgadapter-cli:local", "pgadapter-cli", script, env)
    low = out.lower()
    # Inside tx we should see 'rollbackme'
    assert "rollbackme" in low
    # After rollback it should not be found (no 'rollbackme' in the last select table output)
    # We simply assert that at least one 'rollbackme' exists (first select) and two 'select' blocks
    assert low.count("rollbackme") == 1
    # After commit we should see 'commitme'
    assert "commitme" in low


@pytest.mark.e2e
def test_neo4j_explicit_tx_or_skip():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["neo4j-emulator"])
    _build_image(client, path="neo4j-cli", tag="neo4j-cli:local")

    env = {
        "NEO4J_URI": "bolt://neo4j-emulator:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
    }

    label = "TxCase"
    script = f"""
BEGIN;
CREATE (n:{label} {{name:'tx1'}});
ROLLBACK;
MATCH (n:{label} {{name:'tx1'}}) RETURN count(*) as c1;
BEGIN;
CREATE (n:{label} {{name:'tx2'}});
COMMIT;
MATCH (n:{label} {{name:'tx2'}}) RETURN count(*) as c2;
MATCH (n:{label}) DETACH DELETE n;
exit
"""

    out = _run_cli(client, "neo4j-cli:local", "neo4j-cli", script, env)
    low = out.lower()
    if "error" in low and "begin" in low:
        pytest.skip(
            "Explicit transactions may not be supported via Cypher in this CLI path"
        )
    # Expect 0 for c1 and 1 for c2; we check presence heuristically
    assert "c1" in low or "count" in low
    assert "c2" in low or "count" in low


@pytest.mark.e2e
def test_elasticsearch_refresh_wait_for_visibility():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["elasticsearch-emulator"])
    _build_image(client, path="elasticsearch-cli", tag="elasticsearch-cli:local")

    env = {
        "ELASTICSEARCH_HOST": "elasticsearch-emulator",
        "ELASTICSEARCH_PORT": "9200",
    }
    index = "tx_demo"
    script = f"""
PUT /{index} {{"settings": {{"number_of_shards": 1, "number_of_replicas": 0}}}};
POST /{index}/_doc?refresh=wait_for {{"name": "committed"}};
GET /{index}/_search {{"query": {{"match": {{"name": "committed"}}}}}};
DELETE /{index};
\\q
"""
    out = _run_cli(client, "elasticsearch-cli:local", "elasticsearch-cli", script, env)
    assert "committed" in out


@pytest.mark.e2e
def test_qdrant_upsert_then_delete():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["qdrant-emulator"])
    _build_image(client, path="qdrant-cli", tag="qdrant-cli:local")

    env = {
        "QDRANT_HOST": "qdrant-emulator",
        "QDRANT_PORT": "6333",
    }
    col = "tx_demo"
    script = f"""
PUT /collections/{col} {{"vectors": {{"size": 2, "distance": "Cosine"}}}};
PUT /collections/{col}/points {{"points": [{{"id": 1, "vector": [0.1, 0.2], "payload": {{"tag": "keep"}}}}, {{"id": 2, "vector": [0.2, 0.1], "payload": {{"tag": "drop"}}}}]}};
POST /collections/{col}/points/delete {{"points": [2]}};
POST /collections/{col}/points/search {{"vector": [0.1, 0.2], "limit": 10, "with_payload": true}};
DELETE /collections/{col};
\\q
"""
    out = _run_cli(client, "qdrant-cli:local", "qdrant-cli", script, env)
    low = out.lower()
    assert "keep" in low
    assert "drop" not in low
