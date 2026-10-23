import { CITATION_PREVIEW } from "../config";
import type { AskResponse, Citation } from "../types";
import { RelationText } from "./RelationText";

/** Model answers may use **bold** and the 【 】 brackets some models emit; show plain text. */
export function cleanAnswer(text: string): string {
  return text.replace(/\*\*/g, "").replace(/【/g, "[").replace(/】/g, "]");
}

function preview(text: string): string {
  return text.length > CITATION_PREVIEW ? text.slice(0, CITATION_PREVIEW) + "..." : text;
}

function CitationCard({ citation, maxScore }: { citation: Citation; maxScore: number }) {
  // Scores are cosine similarities or fused ranks depending on the retriever, so the bar is relative.
  const width = maxScore > 0 ? Math.max(8, (citation.score / maxScore) * 100) : 0;
  return (
    <div className="cite">
      <div className="cite-head">
        <span className="cite-id">{citation.chunk_id}</span>
        <span className="cite-via">via {citation.via}</span>
        <span className="score" title="score relative to the best citation">
          {citation.score}
          <span className="bar">
            <i style={{ width: `${width}%` }} />
          </span>
        </span>
      </div>
      <p>{preview(citation.text)}</p>
    </div>
  );
}

/** Meta tags, the answer, the graph paths used and the citations. */
export function AnswerPanel({ result }: { result: AskResponse }) {
  const maxScore = Math.max(0, ...result.citations.map((c) => c.score));
  return (
    <div id="out" className="card">
      <div className="meta" id="meta">
        <span className="tag">{result.kind}-hop</span>
        <span className="tag">retriever: {result.retriever}</span>
        <span className="tag">{result.mode} answer</span>
        <span className={`tag ${result.grounded ? "ok" : "warn"}`}>
          {result.grounded ? "grounded" : "not grounded"}
        </span>
      </div>

      <h2>Answer</h2>
      <p id="answer">{cleanAnswer(result.answer)}</p>

      <h2>Graph paths used</h2>
      <div id="paths" className="paths">
        {result.paths.length ? (
          result.paths.map((p) => (
            <div key={p.text} className="path">
              <RelationText text={p.text} />
            </div>
          ))
        ) : (
          <div className="path none">none (vector retrieval)</div>
        )}
      </div>

      <h2>Citations</h2>
      <div id="cites" className="cites">
        {result.citations.map((c) => (
          <CitationCard key={c.chunk_id} citation={c} maxScore={maxScore} />
        ))}
      </div>
    </div>
  );
}
