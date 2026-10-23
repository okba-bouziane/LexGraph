import pytest
from fastapi.testclient import TestClient

from lexgraph.api import app


@pytest.fixture(scope="module")
def client(db):
    with TestClient(app) as c:
        yield c


def test_health(client):
    h = client.get("/health").json()
    assert h["status"] == "ok" and h["neo4j"] is True and h["graph"]["chunks"] > 0


def test_ask_returns_answer_citations_path_and_subgraph(client):
    r = client.post(
        "/ask",
        json={
            "question": "Which parent company guarantees the supplier's obligations under the Master Supply Agreement?",
            "retriever": "graph",
        },
    )
    assert r.status_code == 200
    d = r.json()
    assert d["answer"] and d["citations"] and d["retriever"] in ("graph", "hybrid")
    assert any("GUA-005" == c["doc_id"] for c in d["citations"])
    assert d["subgraph"]["nodes"] and d["paths"]


def test_ask_validation(client):
    assert client.post("/ask", json={"question": "x"}).status_code == 422
    assert client.post("/ask", json={"question": "valid question here", "retriever": "bogus"}).status_code == 422


def test_entity_endpoint(client):
    d = client.get("/graph/entity/Tassili Emballage SARL").json()
    assert d["type"] == "Party"
    assert any(n["relation"] == "SUBSIDIARY_OF" and n["name"] == "Tafna Industrial Group SPA" for n in d["neighbours"])
    assert client.get("/graph/entity/Nobody Inc").status_code == 404


def test_ingest_rebuilds_graph(client):
    r = client.post("/ingest", json={"extractor": "rules"})
    assert r.status_code == 200 and r.json()["documents"] >= 15
    assert client.get("/health").json()["graph"]["entities"] > 100
