import pytest
from pydantic import ValidationError

from lexgraph.corpus import load_corpus
from lexgraph.extract import LLMExtractor, RuleExtractor, build_registry
from lexgraph.schema import ExtractedEntity, ExtractedRelation, Extraction

DOCS = {d.doc_id: d for d in load_corpus()}
REG = build_registry(list(DOCS.values()))


def rels(ex, relation):
    return {(r.source, r.target) for r in ex.relations if r.relation == relation}


def test_corpus_size_and_labels():
    assert 15 <= len(DOCS) <= 25
    assert all("Sample data, fictional" in d.text for d in DOCS.values())


def test_party_and_roles():
    ex = RuleExtractor().extract(DOCS["MSA-001"], REG)
    assert ("Calder Packaging Ltd", "MSA-001") in rels(ex, "PARTY_TO")
    roles = {r.source: r.properties["role"] for r in ex.relations if r.relation == "PARTY_TO"}
    assert roles["Calder Packaging Ltd"] == "Supplier"


def test_amendment_and_reference_links_resolve_types():
    ex = RuleExtractor().extract(DOCS["MSA-001-A2"], REG)
    assert ("MSA-001-A2", "MSA-001") in rels(ex, "AMENDS")
    assert ("MSA-001-A2", "MSA-001-A1") in rels(ex, "REFERENCES")
    types = {e.name: e.type for e in ex.entities}
    assert types["MSA-001-A2"] == "Amendment" and types["MSA-001"] == "Contract"


def test_ownership_chain():
    ex = RuleExtractor().extract(DOCS["CORP-002"], REG)
    assert ("Calder Packaging Ltd", "Ashford Industrial Group plc") in rels(ex, "SUBSIDIARY_OF")
    pct = [
        r.properties["percent"]
        for r in ex.relations
        if r.source == "Calder Plastics Ltd" and r.relation == "SUBSIDIARY_OF"
    ]
    assert pct == ["60"]


def test_obligation_with_deadline_and_obligee():
    ex = RuleExtractor().extract(DOCS["MSA-001"], REG)
    ob = [e for e in ex.entities if e.type == "Obligation" and "cl.4" in e.name][0]
    assert ob.properties["deadline"] == "30 days"
    assert any(
        r.relation == "OBLIGOR" and r.source == ob.name and r.target == "Brightwater Foods plc" for r in ex.relations
    )
    assert any(
        r.relation == "OBLIGEE" and r.source == ob.name and r.target == "Calder Packaging Ltd" for r in ex.relations
    )


def test_no_bogus_party_from_sentence_fragments():
    ex = RuleExtractor().extract(DOCS["REN-012"], REG)
    parties = {e.name for e in ex.entities if e.type == "Party"}
    assert parties == {"Brightwater Dairy Ltd", "Northwind Logistics Ltd"}


def test_guarantee_and_termination():
    assert ("GUA-005", "MSA-001") in rels(RuleExtractor().extract(DOCS["GUA-005"], REG), "GUARANTEES")
    assert ("NOT-008", "STO-003") in rels(RuleExtractor().extract(DOCS["NOT-008"], REG), "TERMINATES")


def test_every_doc_extracts_with_valid_endpoints():
    for d in DOCS.values():
        ex = RuleExtractor().extract(d, REG)
        names = {e.name for e in ex.entities}
        assert all(r.source in names and r.target in names for r in ex.relations)
        assert any(e.name == d.doc_id for e in ex.entities)


def test_schema_rejects_unknown_types_and_validated_drops_dangling():
    with pytest.raises(ValidationError):
        ExtractedEntity(name="x", type="Planet")  # type: ignore[arg-type]
    ex = Extraction(
        entities=[ExtractedEntity(name="A", type="Party"), ExtractedEntity(name="A", type="Party")],
        relations=[ExtractedRelation(source="A", relation="PARTY_TO", target="Missing")],
    ).validated()
    assert len(ex.entities) == 1 and ex.relations == []


class ScriptedClient:
    """Test double standing in for the LLM client; returns a canned structured result."""

    def structured(self, schema, system, user):
        return schema(
            entities=[
                ExtractedEntity(name="MSA-001", type="Contract"),
                ExtractedEntity(name="Calder Packaging Ltd", type="Party"),
            ],
            relations=[
                ExtractedRelation(source="Calder Packaging Ltd", relation="PARTY_TO", target="MSA-001"),
                ExtractedRelation(source="Calder Packaging Ltd", relation="PARTY_TO", target="Nope"),
            ],
        )


def test_llm_extractor_uses_structured_output_and_validates():
    ex = LLMExtractor(client=ScriptedClient()).extract(DOCS["MSA-001"], REG)
    assert len(ex.relations) == 1
