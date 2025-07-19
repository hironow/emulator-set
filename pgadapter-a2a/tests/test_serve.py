from typer.testing import CliRunner
from unittest.mock import patch


def test_serve_command_starts_server():
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
