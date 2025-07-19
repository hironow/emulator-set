import pytest
from unittest.mock import Mock, patch, AsyncMock


def test_agent_creation_default():
    """Test agent can be created with default connection string."""
    from pgadapter_a2a.agent import CustomAgent

    agent = CustomAgent()
    assert agent is not None
    assert agent.connection_string is None


def test_agent_creation_with_connection_string():
    """Test agent can be created with custom connection string."""
    from pgadapter_a2a.agent import CustomAgent

    connection_string = "postgresql://user:password@localhost/testdb"
    agent = CustomAgent(connection_string=connection_string)

    assert agent is not None
    assert agent.connection_string == connection_string


@pytest.mark.asyncio
async def test_process_query():
    """Test natural language query processing."""
    from pgadapter_a2a.agent import CustomAgent

    agent = CustomAgent()

    with patch("litellm.acompletion") as mock_completion:
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content="SELECT * FROM users;"))]
        )

        sql = await agent.process_query("Show me all users")

        assert sql == "SELECT * FROM users;"
        mock_completion.assert_called_once()


@pytest.mark.asyncio
async def test_process_query_error():
    """Test error handling in query processing."""
    from pgadapter_a2a.agent import CustomAgent

    agent = CustomAgent()

    with patch("litellm.acompletion") as mock_completion:
        mock_completion.side_effect = Exception("LLM service unavailable")

        with pytest.raises(Exception) as exc_info:
            await agent.process_query("Show me all users")

        assert "LLM service unavailable" in str(exc_info.value)


@pytest.mark.asyncio
async def test_execute_sql():
    """Test SQL execution."""
    from pgadapter_a2a.agent import CustomAgent

    agent = CustomAgent(connection_string="postgresql://localhost/test")

    with patch("asyncpg.connect") as mock_connect:
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_connection.fetch.return_value = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]

        result = await agent.execute_sql("SELECT * FROM users;")

        assert len(result) == 2
        assert result[0]["name"] == "Alice"
        assert result[1]["name"] == "Bob"
        mock_connection.close.assert_called_once()


@pytest.mark.asyncio
async def test_execute_sql_error():
    """Test error handling in SQL execution."""
    from pgadapter_a2a.agent import CustomAgent

    agent = CustomAgent(connection_string="postgresql://localhost/test")

    with patch("asyncpg.connect") as mock_connect:
        mock_connection = AsyncMock()
        mock_connect.return_value = mock_connection
        mock_connection.fetch.side_effect = Exception("Table not found")

        with pytest.raises(Exception) as exc_info:
            await agent.execute_sql("SELECT * FROM non_existent_table;")

        assert "Table not found" in str(exc_info.value)
        mock_connection.close.assert_called_once()


@pytest.mark.asyncio
async def test_end_to_end_query():
    """Test end-to-end query execution."""
    from pgadapter_a2a.agent import CustomAgent

    agent = CustomAgent(connection_string="postgresql://localhost/test")

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
