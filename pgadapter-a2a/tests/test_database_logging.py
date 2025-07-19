import pytest
from unittest.mock import patch, AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_agent_logs_database_operations():
    from pgadapter_a2a.agent import DatabaseAgent

    # Create a mock logger
    mock_logger = MagicMock()

    with patch("pgadapter_a2a.agent.logging.getLogger") as mock_get_logger:
        mock_get_logger.return_value = mock_logger

        agent = DatabaseAgent(
            connection_string="postgresql://user:password@localhost/testdb"
        )

        with patch("asyncpg.connect") as mock_connect:
            mock_connection = AsyncMock()
            mock_connect.return_value = mock_connection
            mock_connection.fetch.return_value = [{"id": 1, "name": "Test"}]

            result = await agent.execute_sql("SELECT * FROM test")

            # Check that connection and query were logged
            assert mock_logger.debug.called
            assert mock_logger.info.called

            # Check log messages
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("Executing SQL query" in str(call) for call in log_calls)
            assert any("rows returned" in str(call) for call in log_calls)
