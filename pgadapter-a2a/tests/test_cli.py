import pytest
from typer.testing import CliRunner
from unittest.mock import patch


def test_cli_help():
    """Test CLI help command."""
    from pgadapter_a2a.cli import app

    runner = CliRunner()
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "pgadapter-a2a" in result.stdout
    assert "serve" in result.stdout


def test_serve_command_default():
    """Test serve command with default parameters."""
    from pgadapter_a2a.cli import app

    runner = CliRunner()

    with patch("pgadapter_a2a.cli.uvicorn.run") as mock_run:
        # When there's only one command, Typer makes it the default
        result = runner.invoke(app, [])

        assert result.exit_code == 0
        mock_run.assert_called_once()

        call_args = mock_run.call_args
        assert call_args.kwargs["host"] == "0.0.0.0"
        assert call_args.kwargs["port"] == 8000


def test_serve_command_with_custom_params():
    """Test serve command with custom host, port, and database URL."""
    from pgadapter_a2a.cli import app

    runner = CliRunner()

    with patch("pgadapter_a2a.cli.uvicorn.run") as mock_run:
        result = runner.invoke(
            app,
            [
                "--host",
                "localhost",
                "--port",
                "9000",
                "--database-url",
                "postgresql://test/db",
            ],
        )

        assert result.exit_code == 0
        mock_run.assert_called_once()

        call_args = mock_run.call_args
        assert call_args.kwargs["host"] == "localhost"
        assert call_args.kwargs["port"] == 9000


def test_serve_command_error_handling():
    """Test serve command error handling."""
    from pgadapter_a2a.cli import app

    runner = CliRunner()

    with patch("pgadapter_a2a.cli.create_app") as mock_create_app:
        mock_create_app.side_effect = Exception("Failed to create app")

        result = runner.invoke(app, [])

        assert result.exit_code == 1


@pytest.mark.parametrize(
    "database_url,expected_env",
    [
        ("postgresql://custom/db", "postgresql://custom/db"),
        (None, None),
    ],
)
def test_serve_command_database_url_env(database_url, expected_env):
    """Test that database URL is properly set in environment."""
    from pgadapter_a2a.cli import app
    import os

    runner = CliRunner()

    with patch("pgadapter_a2a.cli.uvicorn.run") as _mock_run:
        with patch.dict(os.environ, {}, clear=True):
            args = []
            if database_url:
                args.extend(["--database-url", database_url])

            result = runner.invoke(app, args)

            assert result.exit_code == 0

            if expected_env:
                assert os.environ.get("DATABASE_URL") == expected_env
            else:
                assert (
                    "DATABASE_URL" not in os.environ
                    or os.environ.get("DATABASE_URL") == ""
                )
