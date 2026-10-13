import { useCallback, useEffect, useState } from 'react';
import { fetchResearchState, type ResearchState } from '../services/api';

/** Loads /research-state with an explicit reload() for retry buttons. */
export function useResearchState() {
  const [state, setState] = useState<ResearchState | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Only sets state from the promise callbacks, so it is safe to call from an effect.
  const load = useCallback(() => {
    fetchResearchState()
      .then(data => {
        setState(data);
        setError(null);
      })
      .catch((err: unknown) => {
        console.error('Failed to fetch research state:', err);
        setState(null);
        setError(err instanceof Error ? err.message : String(err));
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const reload = useCallback(() => {
    setLoading(true);
    load();
  }, [load]);

  return { state, error, loading, reload };
}
