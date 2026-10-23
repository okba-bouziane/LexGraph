"""Threshold gates on retrieval quality (no LLM). Floors sit a little under the measured
numbers in docs/eval-report.md so a real regression fails CI but noise does not."""

import pytest

from lexgraph.evaluation import load_questions, run_retrieval


@pytest.fixture(scope="module")
def results(retriever):
    return run_retrieval(5, retriever)


def test_question_set_shape():
    qs = load_questions()
    assert len(qs) >= 25
    assert sum(q["kind"] == "multi" for q in qs) >= 15 and sum(q["kind"] == "single" for q in qs) >= 10
    assert all(q["gold_docs"] and q["facts"] for q in qs)


def test_vector_baseline_is_solid_on_single_hop(results):
    s = results["vector"]["single"]
    assert s["recall"] >= 0.95 and s["mrr"] >= 0.9


def test_graph_beats_vector_on_multi_hop(results):
    v, g = results["vector"]["multi"], results["graph"]["multi"]
    assert g["recall"] >= 0.85 and g["full"] >= 0.7
    assert g["recall"] > v["recall"] + 0.1 and g["full"] > v["full"] + 0.2


def test_hybrid_beats_vector_on_multi_hop_and_keeps_single_hop(results):
    assert results["hybrid"]["multi"]["recall"] > results["vector"]["multi"]["recall"] + 0.05
    assert results["hybrid"]["single"]["recall"] >= 0.95


def test_overall_mrr_floor(results):
    for name in ("vector", "graph", "hybrid"):
        assert results[name]["all"]["mrr"] >= 0.85
