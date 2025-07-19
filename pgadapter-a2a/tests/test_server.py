def test_pgadapter_a2a_server_responds_to_health_check():
    from pgadapter_a2a.server import create_app

    app = create_app()
    assert app is not None
