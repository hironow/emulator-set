def test_agent_can_connect_to_database():
    from pgadapter_a2a.agent import DatabaseAgent

    connection_string = "postgresql://user:password@localhost/testdb"
    agent = DatabaseAgent(connection_string=connection_string)

    assert agent.connection_string == connection_string
