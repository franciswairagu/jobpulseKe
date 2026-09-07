import { useEffect, useRef, useState, useCallback } from "react";

// Generic "call an api/client.js function, track loading/error/data" hook.
// Keeps pages free of repeated try/catch/useState boilerplate, and gives
// every page the same error + loading UI contract (section 26/27 of the spec).
export function useAsync(fn, deps = []) {
  const [state, setState] = useState({ status: "loading", data: null, error: null });
  const fnRef = useRef(fn);
  fnRef.current = fn;

  const run = useCallback(() => {
    let cancelled = false;
    setState((s) => ({ ...s, status: "loading", error: null }));
    fnRef
      .current()
      .then((data) => {
        if (!cancelled) setState({ status: "success", data, error: null });
      })
      .catch((error) => {
        if (!cancelled) setState({ status: "error", data: null, error });
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  useEffect(() => run(), [run]);

  return { ...state, refetch: run };
}
