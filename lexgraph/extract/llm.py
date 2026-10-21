"""LLM extractor: structured outputs (Pydantic schema) through an OpenAI-compatible endpoint."""

from lexgraph.corpus import Doc
from lexgraph.llm import LLMClient
from lexgraph.schema import DOCUMENT_TYPES, Extraction

SYSTEM = f"""You extract a knowledge graph from one legal document.
Entity types: Party, {", ".join(DOCUMENT_TYPES)}, Clause, Obligation, Date, Person, Jurisdiction.
Use the document ID (e.g. MSA-001) as the entity name for the document itself and for any other
document it refers to. Name parties exactly as written. Dates are ISO (YYYY-MM-DD).
Relations (source -> target): PARTY_TO (Party -> document, properties.role), AMENDS (Amendment ->
Contract), SUPERSEDES, REFERENCES, GUARANTEES (Guarantee -> Contract), TERMINATES (Notice ->
Contract), SUBSIDIARY_OF (child Party -> parent Party, properties.percent), HAS_CLAUSE (document ->
Clause), IMPOSES (Clause -> Obligation), OBLIGOR / OBLIGEE (Obligation -> Party), DATED (document ->
Date, properties.kind = signed|effective|expires), GOVERNED_BY (document -> Jurisdiction), SIGNED
(Person -> document, properties.party). Only extract facts stated in the text. Every relation
endpoint must also be listed in entities."""


class LLMExtractor:
    name = "llm"

    def __init__(self, client: LLMClient | None = None):
        self.client = client or LLMClient()

    def extract(self, doc: Doc, registry: dict[str, str]) -> Extraction:
        known = ", ".join(f"{k} ({v})" for k, v in sorted(registry.items()))
        user = f"Known document IDs and types: {known}\n\nDocument:\n{doc.text}"
        return self.client.structured(Extraction, SYSTEM, user).validated()
