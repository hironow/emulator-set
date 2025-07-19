from unittest.mock import patch


def test_server_can_be_created():
    from pgadapter_a2a.server import create_app

    app = create_app()
    assert app is not None
    assert hasattr(app.state, "db_skill")
    assert hasattr(app.state, "storage")
    assert hasattr(app.state, "broker")


def test_cli_serve_command_works():
    from pgadapter_a2a.cli import app as cli_app
    from typer.testing import CliRunner

    runner = CliRunner()

    with patch("pgadapter_a2a.cli.uvicorn.run") as mock_run:
        result = runner.invoke(cli_app, ["--database-url", "postgresql://test/db"])

        assert result.exit_code == 0
        assert "Starting pgadapter-a2a server" in result.output
        assert "Using database: postgresql://test/db" in result.output
        mock_run.assert_called_once()
