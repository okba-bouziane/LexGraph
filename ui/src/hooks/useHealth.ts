import { useEffect, useState } from "react";

import { getHealth } from "../api/client";
import type { Health } from "../types";

export type HealthState = { kind: "loading" } | { kind: "ok"; health: Health } | { kind: "error" };

/** Loads /health once when the page opens. */
export function useHealth(): HealthState {
  const [state, setState] = useState<HealthState>({ kind: "loading" });
  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then((health) => !cancelled && setState({ kind: "ok", health }))
      .catch(() => !cancelled && setState({ kind: "error" }));
    return () => {
      cancelled = true;
    };
  }, []);
  return state;
}
