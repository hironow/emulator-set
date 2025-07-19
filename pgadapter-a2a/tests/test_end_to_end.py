import pytest
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.asyncio
async def test_agent_processes_natural_language_and_executes_query():
    from pgadapter_a2a.agent import DatabaseAgent

    agent = DatabaseAgent(
        connection_string="postgresql://user:password@localhost/testdb"
    )

    with patch("litellm.acompletion") as mock_completion:
        mock_completion.return_value = Mock(
            choices=[
                Mock(
                    message=Mock(
                        content="SELECT name, email FROM users WHERE active = true;"
                    )
                )
            ]
        )

        with patch("asyncpg.connect") as mock_connect:
            mock_connection = AsyncMock()
            mock_connect.return_value = mock_connection
            mock_connection.fetch.return_value = [
                {"name": "Alice", "email": "alice@example.com"},
                {"name": "Bob", "email": "bob@example.com"},
            ]

            result = await agent.query("Show me all active users with their emails")

            assert len(result) == 2
            assert result[0]["name"] == "Alice"
            assert result[0]["email"] == "alice@example.com"

            mock_completion.assert_called_once()
            mock_connection.fetch.assert_called_once_with(
                "SELECT name, email FROM users WHERE active = true;"
            )
            mock_connection.close.assert_called_once()
