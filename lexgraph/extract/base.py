from typing import Protocol

from lexgraph.corpus import Doc
from lexgraph.schema import DOCUMENT_TYPES, Extraction

# The header "Type" values in the corpus map onto graph labels.
TYPE_ALIASES = {"Corporate": "Memo"}


def doc_type(doc: Doc) -> str:
    raw = doc.meta.get("Type", "Contract")
    t = TYPE_ALIASES.get(raw, raw)
    return t if t in DOCUMENT_TYPES else "Contract"


def build_registry(docs: list[Doc]) -> dict[str, str]:
    """doc id -> document type, so a reference to another document resolves to the right label."""
    return {d.doc_id: doc_type(d) for d in docs}


class Extractor(Protocol):
    name: str

    def extract(self, doc: Doc, registry: dict[str, str]) -> Extraction: ...
