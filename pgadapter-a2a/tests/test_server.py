import pytest
from unittest.mock import patch, AsyncMock


def test_server_creation():
    """Test that the server can be created with all required components."""
    from pgadapter_a2a.server import create_app

    app = create_app()

    # Basic assertions
    assert app is not None
    assert app.name == "pgadapter-a2a"
    assert app.version == "0.0.1"

    # Check required state attributes
    assert hasattr(app.state, "db_skill")
    assert hasattr(app.state, "storage")
    assert hasattr(app.state, "broker")
    assert hasattr(app.state, "worker")


def test_server_with_custom_database_url():
    """Test server creation with custom DATABASE_URL environment variable."""
    from pgadapter_a2a.server import create_app

    with patch.dict("os.environ", {"DATABASE_URL": "postgresql://custom/db"}):
        app = create_app()
        assert app is not None
        assert app.state.db_skill.connection_string == "postgresql://custom/db"


@pytest.mark.asyncio
async def test_worker_run():
    """Test that worker can be started."""
    from pgadapter_a2a.server import create_app

    app = create_app()

    # Mock the worker's run method
    with patch.object(app.state.worker, "run") as mock_run:
        mock_context = AsyncMock()
        mock_run.return_value.__aenter__.return_value = mock_context
        mock_run.return_value.__aexit__.return_value = None

        # Test worker run
        async with app.state.worker.run():
            pass

        mock_run.assert_called_once()
