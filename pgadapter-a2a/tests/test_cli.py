import pytest
from typer.testing import CliRunner


def test_cli_exists():
    from pgadapter_a2a.cli import app
    
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "pgadapter-a2a" in result.stdout