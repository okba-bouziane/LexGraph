import os

os.environ["LLM_API_KEY"] = ""  # tests never call a live model

import pytest

from lexgraph.graph import GraphDB
from lexgraph.ingest import ingest


@pytest.fixture(scope="session")
def db():
    database = GraphDB()
    if not database.ping():
        pytest.skip("Neo4j is not reachable (start it with `docker compose up -d neo4j`)")
    ingest("rules", reset=True, db=database)
    yield database
    database.close()


@pytest.fixture(scope="session")
def retriever(db):
    from lexgraph.retrieval import Retriever

    return Retriever(db)
