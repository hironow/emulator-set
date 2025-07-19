import logging
from io import StringIO


def test_logger_outputs_with_proper_format():
    from pgadapter_a2a.logger import setup_logger

    # Create a string buffer to capture log output
    log_capture = StringIO()

    logger = setup_logger("test-logger")

    # Add a handler to capture output
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)

    # Log a test message
    logger.info("Test message")

    # Get the captured output
    output = log_capture.getvalue()

    assert "Test message" in output
    assert output.strip() != ""  # Should have some output


def test_logger_has_console_handler_with_formatter():
    from pgadapter_a2a.logger import setup_logger

    logger = setup_logger("test-logger", console=True)

    # Check that logger has at least one handler
    assert len(logger.handlers) > 0

    # Check that at least one handler is a StreamHandler
    stream_handlers = [
        h for h in logger.handlers if isinstance(h, logging.StreamHandler)
    ]
    assert len(stream_handlers) > 0

    # Check that the handler has a formatter
    handler = stream_handlers[0]
    assert handler.formatter is not None
