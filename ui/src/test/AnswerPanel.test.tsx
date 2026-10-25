import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { AnswerPanel, cleanAnswer } from "../components/AnswerPanel";
import type { AskResponse } from "../types";

const result: AskResponse = {
  question: "What monthly fee does Sahel Agro now pay Djazair Cloud?",
  answer: "Sahel Agro now pays **1,575,000 DZD** 【CLD-015-A1#1.0】.",
  mode: "llm",
  kind: "multi",
  retriever: "graph",
  grounded: true,
  citations: [{ chunk_id: "CLD-015-A1#1.0", doc_id: "CLD-015-A1", text: "x".repeat(300), score: 0.91, via: "graph" }],
  cited_ids: ["CLD-015-A1#1.0"],
  paths: [{ text: "CLD-015 <-[AMENDS]- CLD-015-A1", nodes: ["CLD-015", "CLD-015-A1"], edges: [] }],
  subgraph: { nodes: [], edges: [] },
  trace: [],
};

describe("AnswerPanel", () => {
  it("removes markdown bold and normalises the CJK brackets", () => {
    expect(cleanAnswer(result.answer)).toBe("Sahel Agro now pays 1,575,000 DZD [CLD-015-A1#1.0].");
  });

  it("turns narrow no-break spaces into normal spaces and separates a glued citation", () => {
    expect(cleanAnswer("Djazair\u202FCloud\u00A0SARL fails to meet[GUA-017#2.0].")).toBe(
      "Djazair Cloud SARL fails to meet [GUA-017#2.0].",
    );
  });

  it("separates a citation glued to a closing quote", () => {
    expect(cleanAnswer('states that "it shall perform"[GUA-017#2.0].')).toBe('states that "it shall perform" [GUA-017#2.0].');
  });

  it("shows the tags, the answer, the path and a shortened citation", () => {
    render(<AnswerPanel result={result} />);
    expect(screen.getByText("multi-hop")).toBeTruthy();
    expect(screen.getByText("grounded").className).toContain("ok");
    expect(screen.getByText(/1,575,000 DZD/)).toBeTruthy();
    expect(document.querySelector(".path")!.textContent).toBe("CLD-015 <-[AMENDS]- CLD-015-A1");
    expect(document.querySelector(".path .rel")!.textContent).toBe("<-[AMENDS]-");
    expect(document.querySelector(".cite")!.textContent).toContain("x".repeat(260) + "...");
  });

  it("says when no graph path was used", () => {
    render(<AnswerPanel result={{ ...result, paths: [], grounded: false }} />);
    expect(screen.getByText("none (vector retrieval)")).toBeTruthy();
    expect(screen.getByText("not grounded").className).toContain("warn");
  });
});
