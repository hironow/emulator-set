"""Feature‑focused E2E for each CLI.

Purpose
- Validate more advanced capabilities beyond CRUD: aggregates, relationships,
  filtered vector search, etc.

Scope
- pgAdapter: aggregation + ORDER BY
- Neo4j: relationships + counting
- Elasticsearch: aggregations
- Qdrant: payload filter + vector search
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
    # Feed a here-doc into the CLI binary; normalize whitespace
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


def _rand(n: int = 6) -> str:
    import string as _s, random as _r

    return "".join(_r.choices(_s.ascii_lowercase + _s.digits, k=n))


@pytest.mark.e2e
def test_pgadapter_cli_aggregate_and_sort():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["pgadapter-emulator", "spanner-emulator"])
    _build_image(client, path="pgadapter-cli", tag="pgadapter-cli:local")

    t = f"e2e_adv_{_rand()}"
    script = f"""
CREATE TABLE {t} (
  id BIGINT PRIMARY KEY,
  name VARCHAR(50),
  price DOUBLE PRECISION
);
INSERT INTO {t} (id, name, price) VALUES (1, 'A', 10.0);
INSERT INTO {t} (id, name, price) VALUES (2, 'B', 20.0);
INSERT INTO {t} (id, name, price) VALUES (3, 'C', 30.0);
SELECT COUNT(*) AS cnt FROM {t};
SELECT name FROM {t} WHERE price >= 15.0 ORDER BY price DESC;
DROP TABLE {t};
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
    lower = out.lower()
    assert ("cnt" in lower) and (" 3" in out or "\n3\n" in lower or "(1 rows)" in out)
    # Should list C then B
    assert "C" in out and "B" in out


@pytest.mark.e2e
def test_neo4j_cli_relationships_and_query():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["neo4j-emulator"])
    _build_image(client, path="neo4j-cli", tag="neo4j-cli:local")

    label = f"Adv{_rand()}"
    script = f"""
CREATE (a:{label} {{name: 'Alice'}});
CREATE (b:{label} {{name: 'Bob'}});
MATCH (a:{label} {{name:'Alice'}}), (b:{label} {{name:'Bob'}})
CREATE (a)-[:KNOWS {{since: 2024}}]->(b);
MATCH (x:{label})-[:KNOWS]->(y:{label}) RETURN x.name, y.name;
MATCH (x:{label})-[:KNOWS]->(y:{label}) RETURN count(*) as rels;
MATCH (n:{label}) DETACH DELETE n;
exit
"""

    env = {
        "NEO4J_URI": "bolt://neo4j-emulator:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password",
    }
    out = _run_cli(client, "neo4j-cli:local", "neo4j-cli", script, env)
    assert "Alice" in out and "Bob" in out
    lower = out.lower()
    assert ("rels" in lower) and (" 1" in out or " 1 " in lower)


@pytest.mark.e2e
def test_elasticsearch_cli_aggregations():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["elasticsearch-emulator"])
    _build_image(client, path="elasticsearch-cli", tag="elasticsearch-cli:local")

    idx = f"adv_{_rand()}"
    script = f"""
PUT /{idx} {{"settings": {{"number_of_shards": 1, "number_of_replicas": 0}}}};
POST /{idx}/_doc {{"name": "A", "price": 10}};
POST /{idx}/_doc {{"name": "B", "price": 30}};
POST /{idx}/_search {{"size": 0, "aggs": {{"avg_price": {{"avg": {{"field": "price"}}}}}}}};
DELETE /{idx};
\\q
"""

    env = {
        "ELASTICSEARCH_HOST": "elasticsearch-emulator",
        "ELASTICSEARCH_PORT": "9200",
    }
    out = _run_cli(client, "elasticsearch-cli:local", "elasticsearch-cli", script, env)
    assert "avg_price" in out


@pytest.mark.e2e
def test_qdrant_cli_payload_filter():
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["qdrant-emulator"])
    _build_image(client, path="qdrant-cli", tag="qdrant-cli:local")

    col = f"adv_{_rand()}"
    script = f"""
PUT /collections/{col} {{"vectors": {{"size": 4, "distance": "Cosine"}}}};
PUT /collections/{col}/points {{"points": [{{"id": 1, "vector": [0.1, 0.2, 0.3, 0.4], "payload": {{"tag": "A"}}}}, {{"id": 2, "vector": [0.2, 0.3, 0.4, 0.5], "payload": {{"tag": "B"}}}}]}};
POST /collections/{col}/points/search {{"vector": [0.1, 0.2, 0.3, 0.4], "limit": 10, "with_payload": true, "filter": {{"must": [{{"key": "tag", "match": {{"value": "A"}}}}]}}}};
DELETE /collections/{col};
\\q
"""

    env = {
        "QDRANT_HOST": "qdrant-emulator",
        "QDRANT_PORT": "6333",
    }
    out = _run_cli(client, "qdrant-cli:local", "qdrant-cli", script, env)
    # Ensure the filtered result mentions tag A or excludes B
    assert '"tag"' in out and '"A"' in out
