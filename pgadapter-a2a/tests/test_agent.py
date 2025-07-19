def test_database_agent_can_be_created():
    from pgadapter_a2a.agent import CustomAgent

    agent = CustomAgent()
    assert agent is not None
