"""LangGraph query flow:

    classify -> choose_retriever -> retrieve -> answer -> self_check --(ungrounded, first try)--> retrieve
                                                                      \\--> END

With an LLM configured, classify/answer/self_check call it. Without one, classification is a
heuristic, the answer is extractive (the best-matching sentences, cited) and the groundedness
check is lexical. `mode` in the output says which path ran.
"""

import re
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from lexgraph import config
from lexgraph.llm import LLMClient
from lexgraph.retrieval import RetrievalResult, Retriever

MULTI_HINTS = re.compile(
    r"\b(parent|owns?|owner|ultimate|ultimately|guarant\w*|amend\w*|renew\w*|since|after|before|"
    r"subcontractor|assign\w*|terminat\w*|notice|settlement|supplier|carrier|provider|came before)\b",
    re.I,
)
META_LINE = re.compile(
    r"^(Document ID|Type|Date|Effective|Expires|Parties|Amends|References|Governing law|Signatories|Guarantees|Terminates|Supersedes):"  # noqa: E501
)
STOP = set(
    "the a an of to and or in on for by is are was were be it its that this with as at from what who "
    "which how when must shall under any each".split()
)


class FlowState(TypedDict, total=False):
    question: str
    forced_retriever: str | None
    k: int
    kind: str
    retriever: str
    result: RetrievalResult
    answer: str
    citations: list[str]
    grounded: bool
    attempts: int
    mode: str
    trace: list[str]


def tokens(text: str) -> set[str]:
    return {t[:6] for t in re.findall(r"[a-z0-9%,.]+", text.lower()) if t not in STOP and len(t) > 1}


def heuristic_kind(question: str) -> str:
    return "multi" if len(MULTI_HINTS.findall(question)) >= 1 else "single"


def extractive_answer(question: str, result: RetrievalResult, n: int = 2) -> tuple[str, list[str]]:
    """Pick the n sentences with most question-word overlap from the retrieved chunks."""
    q = tokens(question)
    cands = []
    for c in result.chunks:
        for sent in re.split(r"(?<=[.!?])\s+|\n+", c.text):
            raw, sent = sent.strip(), sent.strip(" #*")
            if len(sent) > 25 and not raw.startswith(("[", "#", "*")) and not META_LINE.match(raw):
                cands.append((len(q & tokens(sent)) / (1 + len(tokens(sent)) ** 0.5), sent, c.chunk_id))
    cands.sort(key=lambda x: x[0], reverse=True)
    top = cands[:n]
    return " ".join(f"{s} [{cid}]" for _, s, cid in top), [cid for _, _, cid in top]


def lexical_grounded(answer: str, result: RetrievalResult, threshold: float = 0.6) -> bool:
    ans = tokens(re.sub(r"\[[^\]]+\]", "", answer))
    ctx = tokens(" ".join(c.text for c in result.chunks))
    return bool(ans) and len(ans & ctx) / len(ans) >= threshold


def build_flow(retriever: Retriever, llm: LLMClient | None = None, llm_check: bool = True):
    def classify(state: FlowState) -> FlowState:
        q = state["question"]
        kind = heuristic_kind(q)
        if llm and not state.get("forced_retriever"):  # a forced retriever makes the label moot
            try:
                out = (
                    llm.chat(
                        "Classify the legal question. Reply with exactly one word: 'single' if one document "
                        "answers it, 'multi' if it needs facts from several linked documents (amendments, "
                        "guarantees, ownership, references).",
                        q,
                    )
                    .strip()
                    .lower()
                )
                kind = "multi" if "multi" in out else "single"
            except Exception:
                pass
        return {"kind": kind, "attempts": 0, "trace": [f"classify: {kind}"]}

    def choose(state: FlowState) -> FlowState:
        r = state.get("forced_retriever") or ("hybrid" if state["kind"] == "multi" else "vector")
        return {"retriever": r, "trace": state["trace"] + [f"retriever: {r}"]}

    def retrieve(state: FlowState) -> FlowState:
        k = state.get("k") or config.TOP_K
        r = state["retriever"]
        if state["attempts"] > 0:  # retry once, wider, with the graph
            r, k = "hybrid", k * 2
        res = retriever.retrieve(state["question"], r, k)
        return {"result": res, "retriever": r, "trace": state["trace"] + [f"retrieve: {r} k={k}"]}

    def answer(state: FlowState) -> FlowState:
        res = state["result"]
        if llm:
            ctx = "\n\n".join(f"[{c.chunk_id}] {c.text}" for c in res.chunks)
            paths = "\n".join(p.describe() for p in res.paths) or "(none)"
            text = llm.chat(
                "Answer the legal question using ONLY the context. Cite the chunk ids in square brackets "
                "after each claim, e.g. [MSA-001#2.0]. Use the graph paths to connect documents. If the "
                "context does not contain the answer, say so.",
                f"Question: {state['question']}\n\nContext:\n{ctx}\n\nGraph paths:\n{paths}",
            )
            cites = list(dict.fromkeys(re.findall(r"\[([A-Za-z0-9-]+#\d+\.\d+)\]", text)))
            mode = "llm"
        else:
            text, cites = extractive_answer(state["question"], res)
            mode = "extractive"
        return {
            "answer": text,
            "citations": cites,
            "mode": mode,
            "attempts": state["attempts"] + 1,
            "trace": state["trace"] + [f"answer: {mode}"],
        }

    def self_check(state: FlowState) -> FlowState:
        res = state["result"]
        if llm and llm_check:
            ctx = "\n".join(c.text for c in res.chunks)
            try:
                v = (
                    llm.chat(
                        "Reply 'yes' if every claim in the answer is supported by the context, "
                        "otherwise 'no'. One word.",
                        f"Context:\n{ctx}\n\nAnswer:\n{state['answer']}",
                    )
                    .strip()
                    .lower()
                )
                ok = v.startswith("yes")
            except Exception:
                ok = lexical_grounded(state["answer"], res)
        else:
            ok = lexical_grounded(state["answer"], res)
        return {
            "grounded": ok,
            "trace": state["trace"] + [f"self_check: {'grounded' if ok else 'not grounded'}"],
        }

    def after_check(state: FlowState) -> str:
        return END if state["grounded"] or state["attempts"] >= 2 else "retrieve"

    g = StateGraph(FlowState)
    for name, fn in (
        ("classify", classify),
        ("choose", choose),
        ("retrieve", retrieve),
        ("answer", answer),
        ("self_check", self_check),
    ):
        g.add_node(name, fn)
    g.add_edge(START, "classify")
    g.add_edge("classify", "choose")
    g.add_edge("choose", "retrieve")
    g.add_edge("retrieve", "answer")
    g.add_edge("answer", "self_check")
    g.add_conditional_edges("self_check", after_check, {END: END, "retrieve": "retrieve"})
    return g.compile()


def ask(flow, question: str, retriever: str | None = None, k: int | None = None) -> FlowState:
    return flow.invoke({"question": question, "forced_retriever": retriever, "k": k or config.TOP_K})
