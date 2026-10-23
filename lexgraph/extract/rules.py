"""Deterministic rule-based extractor.

It reads the metadata block and clause layout of the sample corpus and needs no network or
key. It is tuned to this corpus format; it is a reproducible baseline and test fixture, not a
general contract parser (see the LLM extractor for free-form text).
"""

import re

from lexgraph.corpus import Doc
from lexgraph.extract.base import doc_type
from lexgraph.schema import ExtractedEntity, ExtractedRelation, Extraction

ROLE_RE = re.compile(r"^(.*?)\s*\(([^()]+)\)\s*$")
OWNS_RE = re.compile(r"^(?P<parent>[^.\n]+?) owns (?P<pct>\d+)% of (?P<child>[^.\n]+?)\.\s*$", re.M)
# Company names end with a legal form: Algerian (SPA, SARL, EURL) or UK-style (Ltd, plc, LP).
LEGAL_FORMS = r"(?:SPA|SARL|EURL|Ltd|plc|LP)"
SHALL_RE = re.compile(rf"(?P<obligor>(?:[A-Z][A-Za-z&']*\s+)*{LEGAL_FORMS}) shall (?P<what>[^.]+)\.")
DEADLINE_RE = re.compile(r"within (\d+) (business days|days|hours)")
SECTION_RE = re.compile(r"^(#{2,3}) (.+)$", re.M)


def _split_list(value: str) -> list[str]:
    return [p.strip() for p in re.split(r"[;,]", value) if p.strip()]


def _aliases(title: str) -> str:
    return title.split(":")[0].strip()


class RuleExtractor:
    name = "rules"

    def extract(self, doc: Doc, registry: dict[str, str]) -> Extraction:
        ents: list[ExtractedEntity] = []
        rels: list[ExtractedRelation] = []
        meta = doc.meta
        dtype = doc_type(doc)
        did = doc.doc_id
        ents.append(
            ExtractedEntity(
                name=did,
                type=dtype,  # type: ignore[arg-type]
                properties={
                    "title": doc.title,
                    **({"alias": _aliases(doc.title)} if dtype not in ("Memo", "Policy") else {}),
                },
            )
        )

        parties: list[str] = []
        for item in _split_list(meta.get("Parties", "")):
            m = ROLE_RE.match(item)
            name, role = (m.group(1), m.group(2)) if m else (item, "")
            parties.append(name)
            ents.append(ExtractedEntity(name=name, type="Party"))
            rels.append(ExtractedRelation(source=name, relation="PARTY_TO", target=did, properties={"role": role}))

        for key, rel in (
            ("Amends", "AMENDS"),
            ("Supersedes", "SUPERSEDES"),
            ("Guarantees", "GUARANTEES"),
            ("Terminates", "TERMINATES"),
            ("References", "REFERENCES"),
        ):
            for target in _split_list(meta.get(key, "")):
                ents.append(
                    ExtractedEntity(name=target, type=registry.get(target, "Contract"))  # type: ignore[arg-type]
                )
                rels.append(ExtractedRelation(source=did, relation=rel, target=target))  # type: ignore[arg-type]

        for key, kind in (("Date", "signed"), ("Effective", "effective"), ("Expires", "expires")):
            if key in meta:
                ents.append(ExtractedEntity(name=meta[key], type="Date"))
                rels.append(
                    ExtractedRelation(source=did, relation="DATED", target=meta[key], properties={"kind": kind})
                )
        if "Governing law" in meta:
            ents.append(ExtractedEntity(name=meta["Governing law"], type="Jurisdiction"))
            rels.append(ExtractedRelation(source=did, relation="GOVERNED_BY", target=meta["Governing law"]))
        for item in _split_list(meta.get("Signatories", "")):
            m = ROLE_RE.match(item)
            if m:
                ents.append(ExtractedEntity(name=m.group(1), type="Person"))
                rels.append(
                    ExtractedRelation(
                        source=m.group(1), relation="SIGNED", target=did, properties={"party": m.group(2)}
                    )
                )

        for m in OWNS_RE.finditer(doc.text):
            parent, child = m.group("parent").strip(), m.group("child").strip()
            ents += [ExtractedEntity(name=parent, type="Party"), ExtractedEntity(name=child, type="Party")]
            rels.append(
                ExtractedRelation(
                    source=child,
                    relation="SUBSIDIARY_OF",
                    target=parent,
                    properties={"percent": m.group("pct")},
                )
            )

        self._clauses(doc, parties, ents, rels)
        return Extraction(entities=ents, relations=rels).validated()

    def _clauses(self, doc: Doc, parties: list[str], ents, rels) -> None:
        body = doc.text
        marks = list(SECTION_RE.finditer(body))
        for i, m in enumerate(marks):
            heading = m.group(2).strip()
            if not (heading.startswith("Clause") or heading == "Notice"):
                continue
            end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
            text = " ".join(body[m.end() : end].split())
            cm = re.match(r"Clause (\d+)", heading)
            cname = f"{doc.doc_id} cl.{cm.group(1)}" if cm else f"{doc.doc_id} notice"
            ents.append(ExtractedEntity(name=cname, type="Clause", properties={"title": heading, "text": text}))
            rels.append(ExtractedRelation(source=doc.doc_id, relation="HAS_CLAUSE", target=cname))
            for sm in SHALL_RE.finditer(text):
                obligor = sm.group("obligor").strip()
                what = sm.group("what").strip()
                sentence = sm.group(0).strip()
                oname = f"{cname} obligation: {obligor} shall {what[:48]}"
                props = {"text": sentence}
                dm = DEADLINE_RE.search(what)
                if dm:
                    props["deadline"] = f"{dm.group(1)} {dm.group(2)}"
                ents.append(ExtractedEntity(name=oname, type="Obligation", properties=props))
                ents.append(ExtractedEntity(name=obligor, type="Party"))
                rels.append(ExtractedRelation(source=cname, relation="IMPOSES", target=oname))
                rels.append(ExtractedRelation(source=oname, relation="OBLIGOR", target=obligor))
                for p in parties:
                    if p != obligor and p in what:
                        rels.append(ExtractedRelation(source=oname, relation="OBLIGEE", target=p))
                        break
