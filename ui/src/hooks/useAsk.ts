import { useCallback, useState } from "react";

import { ask } from "../api/client";
import type { AskResponse, Retriever } from "../types";

/** Sends a question and keeps the latest result, error and loading flag. */
export function useAsk() {
  const [result, setResult] = useState<AskResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = useCallback(async (question: string, retriever: Retriever) => {
    setError("");
    setResult(null);
    setLoading(true);
    try {
      setResult(await ask(question, retriever));
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  return { result, error, loading, submit };
}
