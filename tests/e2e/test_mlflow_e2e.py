import os
from pathlib import Path
import asyncio

import pytest


@pytest.mark.asyncio
async def test_mlflow_e2e_logging_and_persistence(
    http_client, docker_client, ensure_network, require_services
):
    """
    End-to-end check:
    - Write: log params, metrics, and an artifact via MLflow client
    - Read: fetch run and verify values; list artifact
    - Persist: restart container and verify data remains; file exists on host
    """

    ensure_network()
    require_services(["mlflow-server"])

    try:
        import mlflow  # type: ignore
        from mlflow.tracking import MlflowClient  # type: ignore
    except Exception as e:  # pragma: no cover - optional dep
        pytest.skip(f"mlflow client not available: {e}")

    # Point client at local tracking server
    port = os.environ.get("MLFLOW_PORT", "5252")
    os.environ["MLFLOW_TRACKING_URI"] = os.environ.get(
        "MLFLOW_TRACKING_URI", f"http://localhost:{port}"
    )

    # Wait for UI to be reachable (server ready)
    base = f"http://localhost:{port}/"
    for _ in range(60):
        try:
            async with http_client.get(base) as resp:
                if resp.status in (200, 302):
                    break
        except Exception:
            pass
        await asyncio.sleep(1)
    else:
        pytest.skip(f"MLflow UI not reachable at {base}")

    # --- Step 1: Write ---
    experiment_name = "E2E Test"
    expected_params = {"test_run_type": "e2e", "version": "1.0"}
    expected_metrics = {"accuracy": 0.99, "loss": 0.01}

    mlflow.set_experiment(experiment_name)

    # Create and log run
    with mlflow.start_run() as run:
        run_id = run.info.run_id
        mlflow.log_params(expected_params)
        mlflow.log_metrics(expected_metrics)

        # Artifact: greetings/hello.txt
        tmp = Path("hello.txt")
        tmp.write_text("this is a test", encoding="utf-8")
        try:
            mlflow.log_artifact(str(tmp), artifact_path="greetings")
        finally:
            try:
                tmp.unlink()
            except FileNotFoundError:
                pass

    # --- Step 2: Read & Verify ---
    client = MlflowClient()
    run_info = client.get_run(run_id)

    # Params exact match
    assert run_info.data.params.get("test_run_type") == expected_params["test_run_type"]
    assert run_info.data.params.get("version") == expected_params["version"]

    # Metrics approx match (float)
    acc = run_info.data.metrics.get("accuracy")
    loss = run_info.data.metrics.get("loss")
    assert (
        acc is not None and pytest.approx(acc, rel=1e-9) == expected_metrics["accuracy"]
    )
    assert (
        loss is not None and pytest.approx(loss, rel=1e-9) == expected_metrics["loss"]
    )

    # Artifact listing
    artifacts = client.list_artifacts(run_id, path="greetings")
    assert any(a.path.endswith("hello.txt") for a in artifacts)

    # --- Step 3: Persistence ---
    # Host-side artifact root should contain the file
    host_artifacts_root = Path("mlflow-data/artifacts")
    assert host_artifacts_root.exists(), "mlflow-data/artifacts missing on host"
    found = list(host_artifacts_root.rglob("hello.txt"))
    assert found, "Artifact hello.txt not found under mlflow-data/artifacts"

    # Restart only the mlflow container and re-verify the run is accessible
    container = docker_client.containers.get("mlflow-server")
    container.restart()

    # Wait again for readiness
    for _ in range(60):
        try:
            async with http_client.get(base) as resp:
                if resp.status in (200, 302):
                    break
        except Exception:
            pass
        await asyncio.sleep(1)
    else:
        pytest.fail("MLflow UI not reachable after restart")

    # Re-fetch run and verify params still present (persistence)
    run_info_after = client.get_run(run_id)
    assert (
        run_info_after.data.params.get("test_run_type")
        == expected_params["test_run_type"]
    )
