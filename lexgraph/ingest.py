"""Build the graph: chunks with embeddings, extracted entities and relations, provenance links.

Graph shape:
  (:Chunk)-[:FROM_DOC]->(document)      every chunk points at its document entity
  (:Chunk)-[:MENTIONS]->(entity)        chunk text contains the entity (or its clause text)
  (entity)-[typed relations]->(entity)  from the extractor, schema in lexgraph.schema
"""

import re
import sys
from dataclasses import asdict, dataclass

from llama_index.core.graph_stores.types import ChunkNode, EntityNode, Relation

from lexgraph.corpus import Doc, chunk_doc, load_corpus
from lexgraph.embeddings import get_embedder
from lexgraph.extract import Extractor, build_registry, get_extractor
from lexgraph.graph import GraphDB, match_names
from lexgraph.schema import DOCUMENT_TYPES, Extraction, entity_id


@dataclass
class IngestStats:
    extractor: str
    documents: int
    chunks: int
    entities: int
    relations: int
    mentions: int

    def as_dict(self) -> dict:
        return asdict(self)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def build_graph_records(
    doc: Doc, extraction: Extraction, registry: dict[str, str], chunks: list
) -> tuple[list[EntityNode], list[Relation], list[Relation]]:
    """Convert one document's extraction into LlamaIndex nodes and relations (no I/O)."""
    nodes: dict[str, EntityNode] = {}
    for e in extraction.entities:
        eid = entity_id(e.name)
        etype = registry.get(eid, e.type) if e.type in DOCUMENT_TYPES else e.type
        props = {k: v for k, v in e.properties.items() if k != "text"} | {"id": eid}
        prev = nodes.get(eid)
        if prev:
            props = {**prev.properties, **props}
        if etype in ("Party", *DOCUMENT_TYPES):
            props["match_names"] = match_names(e.name, props.get("alias", ""))
        nodes[eid] = EntityNode(name=eid, label=etype, properties=props)

    rels = [
        Relation(
            label=r.relation,
            source_id=entity_id(r.source),
            target_id=entity_id(r.target),
            properties=r.properties,
        )
        for r in extraction.relations
    ]

    texts = {c.id_: _norm(c.text) for c in chunks}
    mentions: list[Relation] = []
    seen: set[tuple[str, str]] = set()
    for c in chunks:
        mentions.append(Relation(label="FROM_DOC", source_id=c.id_, target_id=entity_id(doc.doc_id)))
    clause_text = {e.name: _norm(e.properties.get("text", "")) for e in extraction.entities if e.type == "Clause"}
    for e in extraction.entities:
        eid = entity_id(e.name)
        if eid == doc.doc_id:
            continue
        probe = _norm(e.properties.get("text", "")) or _norm(e.name)
        if e.type == "Obligation":
            probe = _norm(e.properties.get("text", ""))
        for cid, ctext in texts.items():
            hit = probe[:80] in ctext if probe else False
            if e.type == "Clause" and clause_text.get(e.name):
                hit = clause_text[e.name][:80] in ctext
            if hit and (cid, eid) not in seen:
                seen.add((cid, eid))
                mentions.append(Relation(label="MENTIONS", source_id=cid, target_id=eid))
    return list(nodes.values()), rels, mentions


def ingest(
    extractor: Extractor | str = "rules",
    reset: bool = True,
    db: GraphDB | None = None,
    docs: list[Doc] | None = None,
) -> IngestStats:
    if isinstance(extractor, str):
        extractor = get_extractor(extractor)
    docs = docs or load_corpus()
    registry = build_registry(docs)
    own_db = db is None
    db = db or GraphDB()
    try:
        db.ensure_schema()
        if reset:
            db.reset()
        embedder = get_embedder()
        all_chunks = {d.doc_id: chunk_doc(d) for d in docs}
        flat = [c for cs in all_chunks.values() for c in cs]
        vectors = embedder.get_text_embedding_batch([c.text for c in flat], show_progress=False)
        emb = {c.id_: v for c, v in zip(flat, vectors, strict=True)}

        chunk_nodes = [
            ChunkNode(
                text=c.text,
                id_=c.id_,
                label="Chunk",
                embedding=emb[c.id_],
                properties={"doc_id": c.metadata["doc_id"], "title": c.metadata["title"]},
            )
            for c in flat
        ]
        db.store.upsert_nodes(chunk_nodes)

        all_entities: dict[str, EntityNode] = {}
        all_rels: list[Relation] = []
        all_mentions: list[Relation] = []
        for doc in docs:
            extraction = extractor.extract(doc, registry)
            ents, rels, mentions = build_graph_records(doc, extraction, registry, all_chunks[doc.doc_id])
            for e in ents:
                if e.name in all_entities:
                    merged = {**all_entities[e.name].properties, **e.properties}
                    if "alias" in merged:
                        merged["match_names"] = match_names(e.name, merged["alias"])
                    e = EntityNode(name=e.name, label=e.label, properties=merged)
                all_entities[e.name] = e
            all_rels += rels
            all_mentions += mentions
        # Entities first: upserting a relation to a missing node would create it as a Chunk.
        db.store.upsert_nodes(list(all_entities.values()))
        db.store.upsert_relations(all_rels)
        db.store.upsert_relations(all_mentions)
        n_rel, n_men = len(all_rels), len(all_mentions)
        n_ent = len(all_entities)
        return IngestStats(getattr(extractor, "name", "custom"), len(docs), len(flat), n_ent, n_rel, n_men)
    finally:
        if own_db:
            db.close()


if __name__ == "__main__":
    kind = sys.argv[1] if len(sys.argv) > 1 else "rules"
    print(ingest(kind).as_dict())
