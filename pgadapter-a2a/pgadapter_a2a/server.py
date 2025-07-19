from fasta2a import FastA2A
from fasta2a.broker import InMemoryBroker
from fasta2a.storage import InMemoryStorage


def create_app():
    storage = InMemoryStorage()
    broker = InMemoryBroker()
    app = FastA2A(storage=storage, broker=broker)
    return app