import { useCallback, useEffect, useState } from 'react';
import { parseHash, researchTabsEnabled, type Page } from './routes';

export function useHashRoute() {
  const [showResearchTabs] = useState(() =>
    researchTabsEnabled(import.meta.env.VITE_SHOW_RESEARCH_TABS, window.location.search)
  );
  const [page, setPage] = useState<Page>(() => parseHash(window.location.hash, showResearchTabs));

  useEffect(() => {
    const onHashChange = () => setPage(parseHash(window.location.hash, showResearchTabs));
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, [showResearchTabs]);

  const navigate = useCallback((next: Page) => {
    if (window.location.hash !== `#${next}`) {
      window.location.hash = next;
    }
    setPage(next);
  }, []);

  return { page, navigate, showResearchTabs };
}
