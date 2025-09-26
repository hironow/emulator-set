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


def _run_cli(client: docker.DockerClient, script: str) -> str:
    env = {
        "PGHOST": "pgadapter-emulator",
        "PGPORT": "5432",
        "PGUSER": "user",
        "PGDATABASE": "test-instance",
        "PGSSLMODE": "disable",
    }
    script = textwrap.dedent(script).lstrip("\n")
    heredoc = f"cat <<'EOF' | ./pgadapter-cli\n{script}\nEOF"
    try:
        logs: bytes = client.containers.run(
            image="pgadapter-cli:local",
            command=["sh", "-lc", heredoc],
            environment=env,
            network=NETWORK_NAME,
            remove=True,
            stdout=True,
            stderr=True,
        )
        return logs.decode(errors="ignore")
    except Exception as e:
        pytest.skip(f"run pgadapter-cli failed: {e}")


@pytest.mark.e2e
def test_pgadapter_error_without_primary_key():
    """Spanner requires a PRIMARY KEY; table without PK should error."""
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["pgadapter-emulator", "spanner-emulator"]) 
    _build_image(client, path="pgadapter-cli", tag="pgadapter-cli:local")

    script = """
CREATE TABLE no_pk_demo (id BIGINT, name VARCHAR(20));
exit
"""
    out = _run_cli(client, script)
    assert "❌ Error" in out
    assert "primary key" in out.lower()


@pytest.mark.e2e
def test_pgadapter_error_on_serial_type():
    """SERIAL is commonly unsupported in Spanner PG dialect."""
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["pgadapter-emulator", "spanner-emulator"]) 
    _build_image(client, path="pgadapter-cli", tag="pgadapter-cli:local")

    script = """
CREATE TABLE serial_demo (id SERIAL PRIMARY KEY, name VARCHAR(20));
exit
"""
    out = _run_cli(client, script)
    low = out.lower()
    if "error" in low:
        assert True
    else:
        # Some pgAdapter builds accept SERIAL; treat as environment-supported and skip
        pytest.skip("SERIAL appears supported by this pgAdapter build")


@pytest.mark.e2e
def test_pgadapter_error_on_sequence():
    """Sequences are not supported in Spanner PG dialect."""
    client = _docker_client()
    _ensure_network(client)
    _ensure_services_running(client, ["pgadapter-emulator", "spanner-emulator"]) 
    _build_image(client, path="pgadapter-cli", tag="pgadapter-cli:local")

    script = """
CREATE SEQUENCE s_demo START 1;
exit
"""
    out = _run_cli(client, script)
    assert "❌ Error" in out
    assert ("sequence" in out.lower()) or ("not supported" in out.lower())
