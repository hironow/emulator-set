from unittest.mock import patch, MagicMock
from typer.testing import CliRunner


def test_cli_logs_startup_messages():
    from pgadapter_a2a.cli import app as cli_app

    runner = CliRunner()

    with patch("pgadapter_a2a.cli.uvicorn.run") as mock_run:
        with patch("pgadapter_a2a.cli.setup_logger") as mock_setup_logger:
            mock_logger = MagicMock()
            mock_setup_logger.return_value = mock_logger

            result = runner.invoke(cli_app, ["--database-url", "postgresql://test/db"])

            # Check that logger was set up
            mock_setup_logger.assert_called_once_with("pgadapter-a2a", level="INFO")

            # Check that startup messages were logged
            assert mock_logger.info.called
            startup_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any(
                "Starting pgadapter-a2a server" in str(call) for call in startup_calls
            )


def test_cli_accepts_log_level_option():
    from pgadapter_a2a.cli import app as cli_app

    runner = CliRunner()

    with patch("pgadapter_a2a.cli.uvicorn.run") as mock_run:
        with patch("pgadapter_a2a.cli.setup_logger") as mock_setup_logger:
            mock_logger = MagicMock()
            mock_setup_logger.return_value = mock_logger

            result = runner.invoke(cli_app, ["--log-level", "DEBUG"])

            # Check that logger was set up with DEBUG level
            mock_setup_logger.assert_called_once_with("pgadapter-a2a", level="DEBUG")
