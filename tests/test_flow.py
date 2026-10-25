from lexgraph.flow import ask, build_flow, heuristic_kind, lexical_grounded
from lexgraph.retrieval import RetrievalResult, RetrievedChunk


def test_heuristic_kind():
    assert heuristic_kind("Which parent company guarantees the supplier?") == "multi"
    assert heuristic_kind("What colour is the logo?") == "single"


def test_extractive_flow_end_to_end(retriever):
    flow = build_flow(retriever, llm=None)
    out = ask(flow, "How quickly must Zitouna notify Sahel Agro of a personal data breach?")
    assert out["mode"] == "extractive"
    assert "48 hours" in out["answer"]
    assert out["citations"] and out["grounded"] is True
    assert out["trace"][0].startswith("classify") and any("self_check" in t for t in out["trace"])


def test_flow_routes_multi_hop_to_hybrid(retriever):
    out = ask(
        build_flow(retriever, None),
        "Which parent company guarantees the supplier under the Master Supply Agreement?",
    )
    assert out["kind"] == "multi" and out["retriever"] in ("hybrid",)


def test_forced_retriever(retriever):
    out = ask(build_flow(retriever, None), "Who owns Tassili Emballage?", retriever="vector")
    assert out["retriever"] == "vector"


def test_ungrounded_answer_triggers_one_retry(retriever):
    class Liar:
        calls = 0

        def chat(self, system, user, temperature=0.0):
            if "Classify" in system:
                return "single"
            if "supported by the context" in system:
                return "no"
            Liar.calls += 1
            return "The moon is made of cheese."

    out = ask(build_flow(retriever, Liar()), "How quickly must Zitouna notify of a data breach?")
    assert Liar.calls == 2 and out["grounded"] is False
    assert out["trace"].count("retrieve: hybrid k=10") == 1


def test_lexical_groundedness():
    res = RetrievalResult("vector", [RetrievedChunk("c", "d", "Payment is due within 45 days.", 1.0)])
    assert lexical_grounded("Payment is due within 45 days", res)
    assert not lexical_grounded("Elephants wear purple hats daily", res)


class FakeRetriever:
    """Stands in for the Neo4j-backed retriever so the flow logic runs without a database."""

    def __init__(self, text: str):
        self.chunk = RetrievedChunk("DOC-1#0.0", "DOC-1", text, 1.0)
        self.calls: list[tuple[str, int]] = []

    def retrieve(self, question, retriever="hybrid", k=None):
        self.calls.append((retriever, k))
        return RetrievalResult(retriever, [self.chunk])


def test_flow_without_database_answers_and_cites():
    fake = FakeRetriever("The hosting company must report a data breach to the customer within 48 hours of discovery.")
    out = ask(build_flow(fake, llm=None), "Within how many hours must a data breach be reported?", k=3)
    assert out["mode"] == "extractive" and out["grounded"] is True
    assert "48 hours" in out["answer"] and out["citations"] == ["DOC-1#0.0"]
    assert fake.calls == [("vector", 3)]


def test_flow_retries_once_with_hybrid_when_ungrounded():
    class Liar:
        def chat(self, system, user, temperature=0.0):
            return "single" if "Classify" in system else ("no" if "supported by" in system else "Invented claim.")

    fake = FakeRetriever("Payment is due within 45 days.")
    out = ask(build_flow(fake, Liar()), "When is payment due?", k=4)
    assert fake.calls == [("vector", 4), ("hybrid", 8)]
    assert out["grounded"] is False and out["mode"] == "llm"
