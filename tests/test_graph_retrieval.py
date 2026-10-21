from lexgraph.graph import q_entity, q_link_entities


def test_graph_counts(db):
    c = db.counts()
    assert c["chunks"] >= 60 and c["entities"] >= 100 and c["relationships"] > 200


def test_entities_are_not_mislabelled_as_chunks(db):
    assert db.run("MATCH (n:__Entity__:Chunk) RETURN count(n) AS n")[0]["n"] == 0


def test_vector_retrieval_finds_clause(retriever):
    res = retriever.vector("How quickly must Tessellate notify a personal data breach?", 3)
    assert res.chunks[0].doc_id == "DPA-010"


def test_entity_linking_by_alias_and_short_name(db):
    ids = {r["id"] for r in db.run(*q_link_entities("Who owns Calder Packaging under the Master Supply Agreement?"))}
    assert {"Calder Packaging Ltd", "MSA-001"} <= ids


def test_graph_expansion_reaches_guarantee_and_parent(retriever):
    res = retriever.graph(
        "Which parent company guarantees the supplier's obligations under the Master Supply Agreement?", 5
    )
    docs = res.doc_ids()
    assert "GUA-005" in docs and "MSA-001" in docs
    assert any("GUARANTEES" in p.describe() for p in res.paths)


def test_two_hop_ownership_path(retriever):
    res = retriever.graph("Which company owns the carrier under the Transport Services Agreement?", 5)
    assert "CORP-001" in res.doc_ids()
    assert any("CORP-001" in p.node_ids and len(p.edges) >= 2 for p in res.paths)


def test_hybrid_fuses_both(retriever):
    res = retriever.hybrid(
        "How many days does Brightwater Foods now have to pay Calder Packaging invoices under the Master Supply Agreement as amended?",
        5,
    )
    assert {"MSA-001", "MSA-001-A1"} <= set(res.doc_ids())


def test_subgraph_contains_retrieved_docs(retriever):
    res = retriever.graph("Who guarantees the Master Supply Agreement?", 5)
    sg = retriever.subgraph(res)
    ids = {n["id"] for n in sg["nodes"]}
    assert "GUA-005" in ids and any(e["type"] == "GUARANTEES" for e in sg["edges"])


def test_entity_lookup(db):
    e = db.run(*q_entity("calder packaging"))[0]
    assert e["id"] == "Calder Packaging Ltd" and e["type"] == "Party"
