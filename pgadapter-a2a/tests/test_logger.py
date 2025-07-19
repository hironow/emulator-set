import logging


def test_logger_can_be_configured():
    from pgadapter_a2a.logger import setup_logger

    logger = setup_logger("pgadapter-a2a")

    assert logger is not None
    assert logger.name == "pgadapter-a2a"
    assert isinstance(logger, logging.Logger)
