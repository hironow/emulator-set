import os
from fasta2a import FastA2A
from fasta2a.broker import InMemoryBroker
from fasta2a.storage import InMemoryStorage
from .skills import DatabaseAgentSkill


def create_app():
    storage = InMemoryStorage()
    broker = InMemoryBroker()

    # Create the A2A app
    app = FastA2A(storage=storage, broker=broker)

    # Get database connection from environment or use default
    connection_string = os.getenv("DATABASE_URL", "postgresql://localhost/postgres")

    # Create and register the database agent skill
    db_skill = DatabaseAgentSkill(connection_string)

    # Store the skill on the app for later use
    app.state.db_skill = db_skill
    app.state.storage = storage
    app.state.broker = broker

    return app
