import pytest
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.asyncio
async def test_database_agent_skill_can_process_a2a_messages():
    from pgadapter_a2a.skills import DatabaseAgentSkill

    skill = DatabaseAgentSkill(
        connection_string="postgresql://user:password@localhost/testdb"
    )

    with patch("litellm.acompletion") as mock_completion:
        mock_completion.return_value = Mock(
            choices=[
                Mock(message=Mock(content="SELECT COUNT(*) as user_count FROM users;"))
            ]
        )

        with patch("asyncpg.connect") as mock_connect:
            mock_connection = AsyncMock()
            mock_connect.return_value = mock_connection
            mock_connection.fetch.return_value = [{"user_count": 42}]

            result = await skill.execute(
                task_id="test-task-123",
                input_data={"query": "How many users are in the database?"},
            )

            assert result["sql"] == "SELECT COUNT(*) as user_count FROM users;"
            assert result["results"][0]["user_count"] == 42
            assert (
                result["natural_language_query"]
                == "How many users are in the database?"
            )
