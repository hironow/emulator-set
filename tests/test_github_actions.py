import os
import yaml


def test_github_actions_workflow_exists():
    """Test that GitHub Actions workflow file exists."""
    # Get the parent directory of the tests directory
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workflow_path = os.path.join(parent_dir, ".github/workflows/test-emulators.yml")
    assert os.path.exists(workflow_path), (
        f"GitHub Actions workflow file not found at {workflow_path}"
    )


def test_github_actions_workflow_has_docker_compose_steps():
    """Test that workflow contains necessary Docker Compose steps."""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workflow_path = os.path.join(parent_dir, ".github/workflows/test-emulators.yml")

    with open(workflow_path, "r") as f:
        workflow = yaml.safe_load(f)

    # Check basic structure
    assert "jobs" in workflow, "Workflow must have jobs section"
    assert "test" in workflow["jobs"], "Workflow must have test job"

    test_job = workflow["jobs"]["test"]
    assert "steps" in test_job, "Test job must have steps"

    # Check for Docker Compose up step
    steps = test_job["steps"]
    has_docker_compose_up = any(
        "docker-compose up -d" in str(step.get("run", ""))
        or "docker compose up -d" in str(step.get("run", ""))
        for step in steps
    )
    assert has_docker_compose_up, (
        "Workflow must have step to start Docker Compose services"
    )


def test_github_actions_workflow_runs_pytest():
    """Test that workflow runs pytest on test files."""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workflow_path = os.path.join(parent_dir, ".github/workflows/test-emulators.yml")

    with open(workflow_path, "r") as f:
        workflow = yaml.safe_load(f)

    test_job = workflow["jobs"]["test"]
    steps = test_job["steps"]

    # Check for pytest run step
    has_pytest = any(
        "pytest" in str(step.get("run", ""))
        and (
            "test_" in str(step.get("run", "")) or "tests/" in str(step.get("run", ""))
        )
        for step in steps
    )
    assert has_pytest, "Workflow must have step to run pytest on test files"


def test_github_actions_uses_latest_versions():
    """Test that GitHub Actions workflow uses the latest versions of actions."""
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workflow_path = os.path.join(parent_dir, ".github/workflows/test-emulators.yml")

    with open(workflow_path, "r") as f:
        workflow = yaml.safe_load(f)

    test_job = workflow["jobs"]["test"]
    steps = test_job["steps"]

    # Check actions/checkout version
    checkout_step = next(
        (
            step
            for step in steps
            if step.get("uses", "").startswith("actions/checkout@")
        ),
        None,
    )
    assert checkout_step is not None, "Workflow must use actions/checkout"
    assert checkout_step["uses"] == "actions/checkout@v4", (
        "Should use actions/checkout@v4"
    )

    # Check actions/setup-python version
    python_step = next(
        (
            step
            for step in steps
            if step.get("uses", "").startswith("actions/setup-python@")
        ),
        None,
    )
    assert python_step is not None, "Workflow must use actions/setup-python"
    assert python_step["uses"] == "actions/setup-python@v5", (
        "Should use actions/setup-python@v5 (latest)"
    )
