import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_agent_can_execute_query_and_return_results():
    from pgadapter_a2a.agent import DatabaseAgent

    agent = DatabaseAgent(
        connection_string="postgresql://user:password@localhost/testdb"
    )

    with patch("pgadapter_a2a.agent.asyncpg.connect") as mock_connect:
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_connection.fetch.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

        result = await agent.execute_sql("SELECT * FROM users")

        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        mock_connection.close.assert_called_once()
