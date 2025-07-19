import os
import typer
import uvicorn

from .server import create_app
from .logger import setup_logger

app = typer.Typer(name="pgadapter-a2a")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    database_url: str = typer.Option(
        None, "--database-url", "-d", help="Database connection URL"
    ),
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    ),
):
    """Start the pgadapter-a2a server."""
    # Set up logger
    logger = setup_logger("pgadapter-a2a", level=log_level)

    if database_url:
        os.environ["DATABASE_URL"] = database_url
        logger.info(f"Using database: {database_url}")
    else:
        logger.info("Using default database configuration")

    logger.info(f"Starting pgadapter-a2a server on {host}:{port}")

    try:
        a2a_app = create_app()
        logger.info("Server application created successfully")

        # Configure uvicorn logging
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["formatters"]["default"]["fmt"] = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        log_config["formatters"]["access"]["fmt"] = (
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        uvicorn.run(
            a2a_app,
            host=host,
            port=port,
            log_config=log_config,
            log_level=log_level.lower(),
        )
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise typer.Exit(code=1)
