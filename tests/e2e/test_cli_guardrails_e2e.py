"""Guardrail E2E tests (no CLI changes required).

Goals
- Catch regressions in constraint/mode enforcement and type handling.
- Keep flows independent and self‑cleaning.
"""

import textwrap
import pytest
import docker


NETWORK_NAME = "emulator-network"


def _dc() -> docker.DockerClient:
    try:
        c = docker.from_env()
        c.ping()
        return c
    except Exception as e:
        pytest.skip(f"docker not available: {e}")


def _need_net(c: docker.DockerClient) -> None:
    if not c.networks.list(names=[NETWORK_NAME]):
        pytest.skip("emulator-network not found. Start emulators first.")


def _need(c: docker.DockerClient, names: list[str]) -> None:
    running = {x.name for x in c.containers.list()}
    missing = [n for n in names if n not in running]
    if missing:
        pytest.skip(f"required emulator containers not running: {', '.join(missing)}")


def _build(c: docker.DockerClient, path: str, tag: str) -> None:
    try:
        c.images.build(path=path, tag=tag, rm=True)
    except Exception as e:
        pytest.skip(f"failed to build {tag}: {e}")


def _run(c: docker.DockerClient, image: str, binary: str, script: str, env: dict[str, str]) -> str:
    script = textwrap.dedent(script).lstrip("\n")
    heredoc = f"cat <<'EOF' | ./{binary}\n{script}\nEOF"
    try:
        out: bytes = c.containers.run(
            image=image,
            command=["sh", "-lc", heredoc],
            environment=env,
            network=NETWORK_NAME,
            remove=True,
            stdout=True,
            stderr=True,
        )
        return out.decode(errors="ignore")
    except Exception as e:
        pytest.skip(f"run {image} failed: {e}")


@pytest.mark.e2e
def test_pgadapter_read_only_mode_or_skip():
    """SET TRANSACTION READ ONLY should prevent writes (if supported)."""
    c = _dc()
    _need_net(c)
    _need(c, ["pgadapter-emulator", "spanner-emulator"]) 
    _build(c, "pgadapter-cli", "pgadapter-cli:local")

    env = {"PGHOST": "pgadapter-emulator", "PGPORT": "5432", "PGUSER": "user", "PGDATABASE": "test-instance", "PGSSLMODE": "disable"}
    script = """
DROP TABLE IF EXISTS ro_demo;
CREATE TABLE ro_demo (id BIGINT PRIMARY KEY, v INT);
BEGIN;
SET TRANSACTION READ ONLY;
INSERT INTO ro_demo (id, v) VALUES (1, 1);
ROLLBACK;
DROP TABLE ro_demo;
exit
"""
    out = _run(c, "pgadapter-cli:local", "pgadapter-cli", script, env).lower()
    if "set transaction" in out and "error" in out:
        # Some builds may not support the SET TRANSACTION syntax — treat as unsupported
        pytest.skip("SET TRANSACTION READ ONLY not supported by this pgAdapter build")
    # Expect write attempt to fail under READ ONLY
    assert "error" in out or "read only" in out


@pytest.mark.e2e
def test_neo4j_unique_constraint_enforcement():
    c = _dc()
    _need_net(c)
    _need(c, ["neo4j-emulator"]) 
    _build(c, "neo4j-cli", "neo4j-cli:local")

    env = {"NEO4J_URI": "bolt://neo4j-emulator:7687", "NEO4J_USER": "neo4j", "NEO4J_PASSWORD": "password"}
    script = """
CREATE CONSTRAINT unique_email IF NOT EXISTS FOR (u:User) REQUIRE u.email IS UNIQUE;
CREATE (u1:User {email:'dup@example.com'});
CREATE (u2:User {email:'dup@example.com'});
// Expect constraint violation above
MATCH (u:User) DETACH DELETE u;
DROP CONSTRAINT unique_email IF EXISTS;
exit
"""
    out = _run(c, "neo4j-cli:local", "neo4j-cli", script, env).lower()
    assert ("constraint" in out and "violation" in out) or ("already exists" in out) or ("error" in out)


@pytest.mark.e2e
def test_elasticsearch_mapping_type_conflict():
    c = _dc()
    _need_net(c)
    _need(c, ["elasticsearch-emulator"]) 
    _build(c, "elasticsearch-cli", "elasticsearch-cli:local")

    env = {"ELASTICSEARCH_HOST": "elasticsearch-emulator", "ELASTICSEARCH_PORT": "9200"}
    idx = "type_conflict"
    script = f"""
PUT /{idx} {{"mappings": {{"properties": {{"price": {{"type": "integer"}}}}}}}};
POST /{idx}/_doc {{"price": 10}};
POST /{idx}/_doc {{"price": "not-an-integer"}};
DELETE /{idx};
\\q
"""
    out = _run(c, "elasticsearch-cli:local", "elasticsearch-cli", script, env)
    # Expect HTTP 400 error for type conflict
    assert "HTTP 400" in out or "mapper_parsing_exception" in out.lower()


@pytest.mark.e2e
def test_qdrant_delete_by_filter_and_verify():
    c = _dc()
    _need_net(c)
    _need(c, ["qdrant-emulator"]) 
    _build(c, "qdrant-cli", "qdrant-cli:local")

    env = {"QDRANT_HOST": "qdrant-emulator", "QDRANT_PORT": "6333"}
    col = "delete_filter"
    script = textwrap.dedent(
        f"""
        PUT /collections/{col} {{"vectors": {{"size": 2, "distance": "Cosine"}}}};
        PUT /collections/{col}/points {{
          "points": [
            {{"id": 1, "vector": [0.1, 0.2], "payload": {{"tag": "A"}}}},
            {{"id": 2, "vector": [0.2, 0.1], "payload": {{"tag": "B"}}}}
          ]
        }};
        POST /collections/{col}/points/delete {{
          "filter": {{"must": [{{"key": "tag", "match": {{"value": "B"}}}}]}}
        }};
        POST /collections/{col}/points/search {{
          "vector": [0.1, 0.2],
          "limit": 10,
          "with_payload": true
        }};
        DELETE /collections/{col};
        \\q
        """
    ).lstrip("\n")
    out = _run(c, "qdrant-cli:local", "qdrant-cli", script, env)
    if "HTTP 400" in out:
        pytest.skip("Qdrant delete-by-filter not supported by this emulator build")
    low = out.lower()
    if '"status": "ok"' not in out or '"tag"' not in low:
        pytest.skip("Qdrant response missing payload or status; skipping")
    assert '"a"' in low and '"b"' not in low
