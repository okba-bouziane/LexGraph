"""Extraction schema: the entity and relation types the graph is allowed to contain.

The same Pydantic models are the structured-output contract for the LLM extractor and the
return type of the rule-based extractor, so both feed the graph builder identically.
"""

from typing import Literal

from pydantic import BaseModel, Field

EntityType = Literal[
    "Party",
    "Contract",
    "Amendment",
    "Guarantee",
    "Notice",
    "Policy",
    "Memo",
    "Clause",
    "Obligation",
    "Date",
    "Person",
    "Jurisdiction",
]

RelationType = Literal[
    "PARTY_TO",  # Party -> document, property: role
    "AMENDS",  # Amendment -> Contract
    "SUPERSEDES",  # document -> document
    "REFERENCES",  # document -> document
    "GUARANTEES",  # Guarantee -> Contract
    "TERMINATES",  # Notice -> Contract
    "SUBSIDIARY_OF",  # Party -> Party (parent), property: percent
    "HAS_CLAUSE",  # document -> Clause
    "IMPOSES",  # Clause -> Obligation
    "OBLIGOR",  # Obligation -> Party (who must act)
    "OBLIGEE",  # Obligation -> Party (who benefits)
    "DATED",  # document -> Date, property: kind (signed/effective/expires)
    "GOVERNED_BY",  # document -> Jurisdiction
    "SIGNED",  # Person -> document, property: party
]

DOCUMENT_TYPES = ("Contract", "Amendment", "Guarantee", "Notice", "Policy", "Memo")

# Relations followed during graph expansion. Dates and jurisdictions are leaf facts
# shared by many documents, so traversing them would connect everything to everything.
TRAVERSAL_RELATIONS = (
    "PARTY_TO",
    "AMENDS",
    "SUPERSEDES",
    "REFERENCES",
    "GUARANTEES",
    "TERMINATES",
    "SUBSIDIARY_OF",
)


class ExtractedEntity(BaseModel):
    name: str = Field(description="Canonical name, e.g. 'Calder Packaging Ltd' or 'MSA-001'")
    type: EntityType
    properties: dict[str, str] = Field(default_factory=dict)


class ExtractedRelation(BaseModel):
    source: str = Field(description="Name of the source entity (must appear in entities)")
    relation: RelationType
    target: str = Field(description="Name of the target entity (must appear in entities)")
    properties: dict[str, str] = Field(default_factory=dict)


class Extraction(BaseModel):
    entities: list[ExtractedEntity] = Field(default_factory=list)
    relations: list[ExtractedRelation] = Field(default_factory=list)

    def validated(self) -> "Extraction":
        """Drop relations whose endpoints are not extracted entities; dedupe both lists."""
        seen: dict[tuple[str, str], ExtractedEntity] = {}
        for e in self.entities:
            seen.setdefault((e.type, e.name.strip()), e)
        names = {n for _, n in seen}
        rels: dict[tuple[str, str, str], ExtractedRelation] = {}
        for r in self.relations:
            if r.source.strip() in names and r.target.strip() in names:
                rels.setdefault((r.source.strip(), r.relation, r.target.strip()), r)
        return Extraction(entities=list(seen.values()), relations=list(rels.values()))


def entity_id(name: str) -> str:
    """Stable node id. Names are unique across types in this corpus (document IDs, legal
    names, ISO dates, clause references), so the trimmed name is the id."""
    return name.strip()
