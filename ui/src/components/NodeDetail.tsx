import { useEffect, useState } from "react";

import { getEntity } from "../api/client";
import { HIDDEN_NEIGHBOUR_TYPES, MAX_NEIGHBOURS } from "../config";
import type { EntityDetail, Neighbour } from "../types";
import { RelationText } from "./RelationText";

type State = { kind: "idle" } | { kind: "loading" } | { kind: "ok"; entity: EntityDetail } | { kind: "error" };

function describe(n: Neighbour): string {
  const arrow = n.outgoing ? `-[${n.relation}]->` : `<-[${n.relation}]-`;
  return `${arrow} ${n.name}`;
}

/** Details of the node clicked in the graph: type, title and its neighbours. */
export function NodeDetail({ id }: { id: string | null }) {
  const [state, setState] = useState<State>({ kind: "idle" });

  useEffect(() => {
    if (!id) {
      setState({ kind: "idle" });
      return;
    }
    let cancelled = false;
    setState({ kind: "loading" });
    getEntity(id)
      .then((entity) => !cancelled && setState({ kind: "ok", entity }))
      .catch(() => !cancelled && setState({ kind: "error" }));
    return () => {
      cancelled = true;
    };
  }, [id]);

  if (state.kind === "idle") return <div id="detail">Click a node to see its links.</div>;
  if (state.kind === "loading") return <div id="detail">Loading {id}...</div>;
  if (state.kind === "error") return <div id="detail">Could not load entity.</div>;

  const { entity } = state;
  const neighbours = entity.neighbours
    .filter((n) => !HIDDEN_NEIGHBOUR_TYPES.includes(n.type))
    .slice(0, MAX_NEIGHBOURS);
  return (
    <div id="detail" className="filled">
      <div className="title">
        {entity.id} ({entity.type}){entity.properties.title ? ` - ${entity.properties.title}` : ""}
      </div>
      <ul>
        {neighbours.map((n) => (
          <li key={`${n.relation}-${n.id}-${n.outgoing}`}>
            <RelationText text={describe(n)} />
          </li>
        ))}
      </ul>
    </div>
  );
}
