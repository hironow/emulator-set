import pytest
import subprocess
import time
import docker


def test_qdrant_cli_can_connect():
    """Test that qdrant-cli can connect to Qdrant server."""
    client = docker.from_env()
    
    # Check if qdrant container is running
    try:
        container = client.containers.get('qdrant-emulator')
        assert container.status == 'running', "Qdrant container must be running"
    except docker.errors.NotFound:
        pytest.skip("Qdrant container not running. Run 'docker compose up qdrant' first.")
    
    # Run qdrant-cli with a simple command
    result = subprocess.run(
        ['docker', 'compose', 'run', '--rm', 'qdrant-cli', './qdrant-cli'],
        input=b'\\i\n\\q\n',
        capture_output=True,
        timeout=10
    )
    
    # Check that the command executed successfully
    assert result.returncode == 0, f"qdrant-cli failed with return code {result.returncode}"
    
    # Check output contains expected strings
    output = result.stdout.decode('utf-8')
    assert 'Connected to Qdrant' in output, "CLI should show connection message"
    assert 'Cluster Information:' in output, "CLI should show cluster info"
    assert 'Bye!' in output, "CLI should exit gracefully"


def test_qdrant_cli_can_create_collection():
    """Test that qdrant-cli can create and list collections."""
    client = docker.from_env()
    
    # Check if qdrant container is running
    try:
        container = client.containers.get('qdrant-emulator')
        assert container.status == 'running', "Qdrant container must be running"
    except docker.errors.NotFound:
        pytest.skip("Qdrant container not running. Run 'docker compose up qdrant' first.")
    
    # Create a test collection and list it
    commands = b'''PUT /collections/test_cli_collection {"vectors": {"size": 4, "distance": "Cosine"}};
\\l
DELETE /collections/test_cli_collection;
\\q
'''
    
    result = subprocess.run(
        ['docker', 'compose', 'run', '--rm', 'qdrant-cli', './qdrant-cli'],
        input=commands,
        capture_output=True,
        timeout=15
    )
    
    # Check that the command executed successfully
    assert result.returncode == 0, f"qdrant-cli failed with return code {result.returncode}"
    
    # Check output contains expected results
    output = result.stdout.decode('utf-8')
    assert '"status": "ok"' in output, "Collection creation should return ok status"
    assert 'test_cli_collection' in output, "Collection should appear in list"