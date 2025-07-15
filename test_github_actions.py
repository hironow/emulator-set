import pytest
import os
import yaml


def test_github_actions_workflow_exists():
    """Test that GitHub Actions workflow file exists."""
    workflow_path = ".github/workflows/test-emulators.yml"
    assert os.path.exists(workflow_path), f"GitHub Actions workflow file not found at {workflow_path}"


def test_github_actions_workflow_has_docker_compose_steps():
    """Test that workflow contains necessary Docker Compose steps."""
    workflow_path = ".github/workflows/test-emulators.yml"
    
    with open(workflow_path, 'r') as f:
        workflow = yaml.safe_load(f)
    
    # Check basic structure
    assert 'jobs' in workflow, "Workflow must have jobs section"
    assert 'test' in workflow['jobs'], "Workflow must have test job"
    
    test_job = workflow['jobs']['test']
    assert 'steps' in test_job, "Test job must have steps"
    
    # Check for Docker Compose up step
    steps = test_job['steps']
    has_docker_compose_up = any(
        'docker-compose up -d' in str(step.get('run', '')) or
        'docker compose up -d' in str(step.get('run', ''))
        for step in steps
    )
    assert has_docker_compose_up, "Workflow must have step to start Docker Compose services"


def test_github_actions_workflow_runs_pytest():
    """Test that workflow runs pytest on test files."""
    workflow_path = ".github/workflows/test-emulators.yml"
    
    with open(workflow_path, 'r') as f:
        workflow = yaml.safe_load(f)
    
    test_job = workflow['jobs']['test']
    steps = test_job['steps']
    
    # Check for pytest run step
    has_pytest = any(
        'pytest' in str(step.get('run', '')) and 'test_' in str(step.get('run', ''))
        for step in steps
    )
    assert has_pytest, "Workflow must have step to run pytest on test files"