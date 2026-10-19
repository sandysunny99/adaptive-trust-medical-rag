/**
 * Hash routes and the research-tabs developer flag.
 *
 * Public routes: #analyze (default), #history, #about.
 * Developer routes: #evaluation and #audit, only when the research tabs are
 * enabled with VITE_SHOW_RESEARCH_TABS=true or a ?debug=1 query parameter.
 * Anything else falls back to #analyze.
 */

export type Page = 'analyze' | 'history' | 'about' | 'evaluation' | 'audit';

export const DEFAULT_PAGE: Page = 'analyze';

const PUBLIC_PAGES: readonly Page[] = ['analyze', 'history', 'about'];
const RESEARCH_PAGES: readonly Page[] = ['evaluation', 'audit'];

export function researchTabsEnabled(envFlag: string | undefined, search: string): boolean {
  if (envFlag === 'true') return true;
  return new URLSearchParams(search).get('debug') === '1';
}

export function parseHash(hash: string, showResearchTabs: boolean): Page {
  const name = hash.replace(/^#\/?/, '').toLowerCase();
  if ((PUBLIC_PAGES as readonly string[]).includes(name)) return name as Page;
  if (showResearchTabs && (RESEARCH_PAGES as readonly string[]).includes(name)) return name as Page;
  return DEFAULT_PAGE;
}
