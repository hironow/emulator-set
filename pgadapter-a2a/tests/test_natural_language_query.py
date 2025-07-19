import pytest
from unittest.mock import Mock, patch


@pytest.mark.asyncio
async def test_agent_can_process_natural_language_query():
    from pgadapter_a2a.agent import DatabaseAgent

    agent = DatabaseAgent()

    with patch("litellm.acompletion") as mock_completion:
        mock_completion.return_value = Mock(
            choices=[Mock(message=Mock(content="SELECT * FROM users;"))]
        )

        result = await agent.process_query("Show me all users")

        assert result == "SELECT * FROM users;"
        mock_completion.assert_called_once()
