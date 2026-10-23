import { API_BASE } from "../config";
import type { HealthState } from "../hooks/useHealth";

/** Status badges in the header: Neo4j, graph size and the model in use. */
export function StatusLine({ state }: { state: HealthState }) {
  if (state.kind === "loading") return <div id="status" />;
  if (state.kind === "error") {
    return (
      <div id="status">
        <span className="pill">
          <i className="led down" />
          API not reachable at {API_BASE}
        </span>
      </div>
    );
  }
  const { neo4j, graph, llm_configured, llm_model } = state.health;
  return (
    <div id="status">
      <span className="pill">
        <i className={`led ${neo4j ? "up" : "down"}`} />
        neo4j {neo4j ? "up" : "down"}
      </span>
      <span className="pill">{graph.entities ?? 0} entities</span>
      <span className="pill">{graph.chunks ?? 0} chunks</span>
      <span className="pill">LLM {llm_configured ? llm_model : "not configured (extractive answers)"}</span>
    </div>
  );
}
