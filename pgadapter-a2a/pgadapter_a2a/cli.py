import typer
import uvicorn

from .server import create_app

app = typer.Typer(name="pgadapter-a2a")


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Host to bind to"),
    port: int = typer.Option(8000, help="Port to bind to"),
):
    """Start the pgadapter-a2a server."""
    typer.echo(f"Starting pgadapter-a2a server on {host}:{port}")
    a2a_app = create_app()
    uvicorn.run(a2a_app, host=host, port=port)