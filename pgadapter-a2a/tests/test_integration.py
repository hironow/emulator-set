import pytest
from unittest.mock import Mock, patch, AsyncMock


def test_server_creation_with_logging():
    from pgadapter_a2a.server import create_app

    app = create_app()
    assert app is not None


@pytest.mark.asyncio
async def test_agent_works_with_logging():
    from pgadapter_a2a.agent import DatabaseAgent

    agent = DatabaseAgent(
        connection_string="postgresql://user:password@localhost/testdb"
    )

    with patch("litellm.acompletion") as mock_completion:
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content="SELECT COUNT(*) FROM users;"))]
        )

        with patch("asyncpg.connect") as mock_connect:
            mock_connection = AsyncMock()
            mock_connect.return_value = mock_connection
            mock_connection.fetch.return_value = [{"count": 42}]

            result = await agent.query("How many users do we have?")

            assert len(result) == 1
            assert result[0]["count"] == 42
