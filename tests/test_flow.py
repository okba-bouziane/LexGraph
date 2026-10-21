from lexgraph.flow import ask, build_flow, heuristic_kind, lexical_grounded
from lexgraph.retrieval import RetrievalResult, RetrievedChunk


def test_heuristic_kind():
    assert heuristic_kind("Which parent company guarantees the supplier?") == "multi"
    assert heuristic_kind("What colour is the logo?") == "single"


def test_extractive_flow_end_to_end(retriever):
    flow = build_flow(retriever, llm=None)
    out = ask(flow, "How quickly must Tessellate notify Brightwater Foods of a personal data breach?")
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
    out = ask(build_flow(retriever, None), "Who owns Calder Packaging?", retriever="vector")
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

    out = ask(build_flow(retriever, Liar()), "How quickly must Tessellate notify of a data breach?")
    assert Liar.calls == 2 and out["grounded"] is False
    assert out["trace"].count("retrieve: hybrid k=10") == 1


def test_lexical_groundedness():
    res = RetrievalResult("vector", [RetrievedChunk("c", "d", "Payment is due within 45 days.", 1.0)])
    assert lexical_grounded("Payment is due within 45 days", res)
    assert not lexical_grounded("Elephants wear purple hats daily", res)
