import { useCallback, useEffect, useState } from 'react';
import {
  applyTheme,
  readStoredPreference,
  resolveTheme,
  storePreference,
  type ResolvedTheme,
  type ThemePreference,
} from './theme';

export function useTheme() {
  const [preference, setPreference] = useState<ThemePreference>(readStoredPreference);
  const [resolved, setResolved] = useState<ResolvedTheme>(() => resolveTheme(readStoredPreference()));

  useEffect(() => {
    applyTheme(resolved);
  }, [resolved]);

  // Follow the operating system while no explicit choice is stored.
  useEffect(() => {
    if (preference !== 'system' || typeof window.matchMedia !== 'function') return;
    const query = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => setResolved(query.matches ? 'dark' : 'light');
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, [preference]);

  const toggle = useCallback(() => {
    const next: ResolvedTheme = resolved === 'dark' ? 'light' : 'dark';
    setPreference(next);
    setResolved(next);
    storePreference(next);
  }, [resolved]);

  return { preference, resolved, toggle };
}
