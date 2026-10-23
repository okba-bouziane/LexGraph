import { useEffect, useRef } from "react";
import { DataSet, Network, type Edge, type Node, type Options } from "vis-network/standalone";

import { COLORS } from "../config";
import type { Subgraph, SubgraphEdge, SubgraphNode } from "../types";

const FALLBACK_COLOR = "#888";

/** Colours from the CSS theme, so the graph follows light and dark mode. */
function theme() {
  const css = getComputedStyle(document.documentElement);
  const v = (name: string) => css.getPropertyValue(name).trim();
  return { panel: v("--card-2"), mute: v("--mute"), ink: v("--ink"), line: v("--line") };
}

function toVisNode(n: SubgraphNode): Node {
  const color = COLORS[n.type] || FALLBACK_COLOR;
  return {
    id: n.id,
    label: n.name,
    title: n.title || n.type,
    shape: n.type === "Party" ? "ellipse" : "box",
    margin: { top: 8, right: 12, bottom: 8, left: 12 },
    shapeProperties: { borderRadius: 8 },
    color: {
      background: color,
      border: n.retrieved ? "#ffffff" : color,
      highlight: { background: color, border: "#ffffff" },
      hover: { background: color, border: "#ffffff" },
    },
    borderWidth: n.retrieved ? 3 : 1, // documents whose chunks were retrieved get a white ring
    font: { color: "#fff", size: 14, face: "system-ui, sans-serif" },
    shadow: { enabled: true, color: "rgba(0,0,0,0.25)", size: 8, x: 0, y: 2 },
  };
}

function toVisEdge(e: SubgraphEdge, i: number, t: ReturnType<typeof theme>): Edge {
  return {
    id: i,
    from: e.source,
    to: e.target,
    label: e.type + (e.role ? ` (${e.role})` : ""),
    arrows: { to: { enabled: true, scaleFactor: 0.6 } },
    color: { color: t.mute, highlight: t.ink, hover: t.ink, opacity: 0.7 },
    width: 1.4,
    // The label sits above the line with a halo in the panel colour, so it never runs into the arrow.
    font: { size: 11, align: "top", color: t.mute, strokeWidth: 5, strokeColor: t.panel, face: "ui-monospace, monospace" },
    smooth: { enabled: true, type: "dynamic", roundness: 0.5 },
  };
}

const OPTIONS: Options = {
  physics: {
    solver: "forceAtlas2Based",
    forceAtlas2Based: { gravitationalConstant: -90, springLength: 190, springConstant: 0.05, avoidOverlap: 0.9 },
    stabilization: { iterations: 250 },
  },
  edges: { length: 210 },
  interaction: { hover: true, tooltipDelay: 150 },
  layout: { improvedLayout: true },
};

interface Props {
  subgraph: Subgraph | null;
  onSelect: (id: string) => void;
}

function EmptyState() {
  return (
    <div className="empty">
      <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true">
        <circle cx="5" cy="6" r="2.5" />
        <circle cx="19" cy="6" r="2.5" />
        <circle cx="12" cy="18" r="2.5" />
        <path d="M7.3 7.2 10.6 16M16.7 7.2 13.4 16M7.5 6h9" />
      </svg>
      Ask a question to see the entities and relations behind the answer.
    </div>
  );
}

/** The entities and relations behind the answer, drawn with vis-network. */
export function GraphView({ subgraph, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!subgraph || !container.current) return;
    const t = theme();
    const network = new Network(
      container.current,
      {
        nodes: new DataSet<Node>(subgraph.nodes.map(toVisNode)),
        edges: new DataSet<Edge>(subgraph.edges.map((e, i) => toVisEdge(e, i, t))),
      },
      OPTIONS,
    );
    network.once("stabilizationIterationsDone", () => network.fit({ animation: { duration: 400, easingFunction: "easeInOutQuad" } }));
    network.on("click", (params: { nodes: (string | number)[] }) => {
      if (params.nodes.length) onSelect(String(params.nodes[0]));
    });
    return () => network.destroy();
  }, [subgraph, onSelect]);

  return <div id="graph">{subgraph ? <div ref={container} className="canvas" /> : <EmptyState />}</div>;
}
