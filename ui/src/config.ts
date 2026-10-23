// Settings shared by the UI.

// API base URL: ?api=... in the page URL, then VITE_API_URL at build time, then the local default.
export const API_BASE =
  new URLSearchParams(window.location.search).get("api") ||
  import.meta.env.VITE_API_URL ||
  "http://localhost:8001";

// Node colours in the graph view, one per entity type.
export const COLORS: Record<string, string> = {
  Party: "#2457d6",
  Contract: "#157347",
  Amendment: "#b45309",
  Guarantee: "#8a3ffc",
  Notice: "#c2410c",
  Policy: "#657080",
  Memo: "#0e7490",
};

// Clickable example questions under the form.
export const SAMPLES = [
  "Which company guarantees Djazair Cloud's obligations under the Cloud Hosting Agreement?",
  "What monthly fee does Sahel Agro now pay Djazair Cloud under the Cloud Hosting Agreement as amended?",
  "Which parent company guarantees the supplier's obligations under the Master Supply Agreement?",
  "Which company owns the carrier under the Transport Services Agreement?",
  "Which data centre are the Sahel Agro systems moving to?",
];

export const RETRIEVER_OPTIONS = [
  { value: "auto", label: "auto (flow chooses)" },
  { value: "vector", label: "vector only" },
  { value: "graph", label: "graph-augmented" },
  { value: "hybrid", label: "hybrid" },
] as const;

// Neighbour types left out of the node detail (many of them, not useful for navigation).
export const HIDDEN_NEIGHBOUR_TYPES = ["Clause", "Obligation"];
export const MAX_NEIGHBOURS = 14;
export const CITATION_PREVIEW = 260;
