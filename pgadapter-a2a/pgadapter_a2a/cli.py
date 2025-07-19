import os
import typer
import uvicorn

from .server import create_app

app = typer.Typer(name="pgadapter-a2a")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
    database_url: str = typer.Option(
        None, "--database-url", "-d", help="Database connection URL"
    ),
):
    """Start the pgadapter-a2a server."""
    if database_url:
        os.environ["DATABASE_URL"] = database_url

    typer.echo(f"Starting pgadapter-a2a server on {host}:{port}")
    if database_url:
        typer.echo(f"Using database: {database_url}")

    a2a_app = create_app()
    uvicorn.run(a2a_app, host=host, port=port)
