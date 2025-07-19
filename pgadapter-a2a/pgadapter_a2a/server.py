import os
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fasta2a import FastA2A, Worker
from fasta2a.broker import InMemoryBroker
from fasta2a.schema import Artifact, Message, TaskIdParams, TaskSendParams, TextPart
from fasta2a.storage import InMemoryStorage

from .skills import DatabaseAgentSkill
from .logger import setup_logger

Context = list[Message]
"""The shape of the context you store in the storage."""


class DatabaseWorker(Worker[Context]):
    def __init__(self, *args, db_skill: DatabaseAgentSkill, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_skill = db_skill
        self.logger = setup_logger("pgadapter-a2a.worker")

    async def run_task(self, params: TaskSendParams) -> None:
        task = await self.storage.load_task(params["id"])
        assert task is not None

        await self.storage.update_task(task["id"], state="working")

        context = await self.storage.load_context(task["context_id"]) or []
        context.extend(task.get("history", []))

        # Extract query from the last user message
        query = None
        for msg in reversed(context):
            if msg["role"] == "user":
                for part in msg.get("parts", []):
                    if part.get("kind") == "text":
                        query = part.get("text")
                        break
                if query:
                    break

        if not query:
            # If no query in context, check task params
            query = task.get("input", {}).get("query")

        if not query:
            error_msg = "No query provided"
            message = Message(
                role="agent",
                parts=[TextPart(text=error_msg, kind="text")],
                kind="message",
                message_id=str(uuid.uuid4()),
            )
        else:
            try:
                # Execute the database query
                result = await self.db_skill.execute(task["id"], {"query": query})

                # Format the response
                response_text = (
                    f"SQL Query: {result['sql']}\n\nResults: {result['results']}"
                )
                message = Message(
                    role="agent",
                    parts=[TextPart(text=response_text, kind="text")],
                    kind="message",
                    message_id=str(uuid.uuid4()),
                )
            except Exception as e:
                self.logger.error(f"Error executing query: {e}")
                message = Message(
                    role="agent",
                    parts=[TextPart(text=f"Error: {str(e)}", kind="text")],
                    kind="message",
                    message_id=str(uuid.uuid4()),
                )

        # Update the new message to the context
        context.append(message)

        artifacts = self.build_artifacts(None)
        await self.storage.update_context(task["context_id"], context)
        await self.storage.update_task(
            task["id"],
            state="completed",
            new_messages=[message],
            new_artifacts=artifacts,
        )

    async def cancel_task(self, params: TaskIdParams) -> None:
        task_id = params["id"]
        await self.storage.update_task(task_id, state="cancelled")

    def build_message_history(self, history: list[Message]) -> list[Any]:
        return history

    def build_artifacts(self, result: Any) -> list[Artifact]:
        return []


def create_app():
    storage = InMemoryStorage()
    broker = InMemoryBroker()

    # Get database connection from environment or use default
    connection_string = os.getenv("DATABASE_URL", "postgresql://localhost/postgres")

    # Create and register the database agent skill
    db_skill = DatabaseAgentSkill(connection_string)

    # Create worker
    worker = DatabaseWorker(storage=storage, broker=broker, db_skill=db_skill)

    @asynccontextmanager
    async def lifespan(app: FastA2A) -> AsyncIterator[None]:
        async with app.task_manager:
            async with worker.run():
                yield

    # Create the A2A app with lifespan
    app = FastA2A(storage=storage, broker=broker, lifespan=lifespan)

    # Store references on the app for later use
    app.state.db_skill = db_skill
    app.state.storage = storage
    app.state.broker = broker
    app.state.worker = worker

    return app
