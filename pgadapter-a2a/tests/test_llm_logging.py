import pytest
from unittest.mock import Mock, patch, MagicMock


@pytest.mark.asyncio
async def test_agent_logs_llm_interactions():
    from pgadapter_a2a.agent import DatabaseAgent

    # Create a mock logger
    mock_logger = MagicMock()

    with patch("pgadapter_a2a.agent.logging.getLogger") as mock_get_logger:
        mock_get_logger.return_value = mock_logger

        agent = DatabaseAgent(
            connection_string="postgresql://user:password@localhost/testdb"
        )

        with patch("litellm.acompletion") as mock_completion:
            mock_completion.return_value = Mock(
                choices=[
                    Mock(
                        message=Mock(content="SELECT * FROM users WHERE active = true;")
                    )
                ]
            )

            result = await agent.process_query("Show me active users")

            # Check that LLM interaction was logged
            assert mock_logger.info.called

            # Check log messages
            log_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any(
                "Processing natural language query" in str(call) for call in log_calls
            )
            assert any("Generated SQL" in str(call) for call in log_calls)
            assert any("Show me active users" in str(call) for call in log_calls)
            assert any(
                "SELECT * FROM users WHERE active = true;" in str(call)
                for call in log_calls
            )
