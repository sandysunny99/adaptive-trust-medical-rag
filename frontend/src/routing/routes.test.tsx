import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { parseHash, researchTabsEnabled } from './routes';
import { Layout } from '../components/Layout';

describe('research tabs dev flag', () => {
  it('is off by default', () => {
    expect(researchTabsEnabled(undefined, '')).toBe(false);
    expect(researchTabsEnabled('false', '?debug=0')).toBe(false);
  });

  it('turns on with VITE_SHOW_RESEARCH_TABS=true or ?debug=1', () => {
    expect(researchTabsEnabled('true', '')).toBe(true);
    expect(researchTabsEnabled(undefined, '?debug=1')).toBe(true);
    expect(researchTabsEnabled(undefined, '?foo=bar&debug=1')).toBe(true);
  });

  it('hides Evaluation and Research Audit from the nav when off', () => {
    render(<Layout currentPage="analyze" onNavigate={() => {}}>content</Layout>);
    const nav = screen.getByRole('navigation', { name: 'Main' });
    expect(nav).toHaveTextContent('Analyze');
    expect(nav).toHaveTextContent('History');
    expect(nav).toHaveTextContent('About');
    expect(screen.queryByRole('link', { name: /Evaluation/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Research Audit/ })).not.toBeInTheDocument();
  });

  it('shows Evaluation and Research Audit in the nav when on', () => {
    render(<Layout currentPage="analyze" onNavigate={() => {}} showResearchTabs>content</Layout>);
    expect(screen.getByRole('link', { name: /Evaluation/ })).toHaveAttribute('href', '#evaluation');
    expect(screen.getByRole('link', { name: /Research Audit/ })).toHaveAttribute('href', '#audit');
  });

  it('marks the current page with aria-current', () => {
    render(<Layout currentPage="history" onNavigate={() => {}}>content</Layout>);
    expect(screen.getByRole('link', { name: /History/ })).toHaveAttribute('aria-current', 'page');
    expect(screen.getByRole('link', { name: /^Analyze$/ })).not.toHaveAttribute('aria-current');
  });
});

describe('parseHash', () => {
  it('maps public hashes and falls back to analyze for unknown ones', () => {
    expect(parseHash('#history', false)).toBe('history');
    expect(parseHash('#about', false)).toBe('about');
    expect(parseHash('#analyze', false)).toBe('analyze');
    expect(parseHash('', false)).toBe('analyze');
    expect(parseHash('#nonsense', false)).toBe('analyze');
    expect(parseHash('#evidence', false)).toBe('analyze');
  });

  it('only allows research routes when the flag is on', () => {
    expect(parseHash('#evaluation', false)).toBe('analyze');
    expect(parseHash('#audit', false)).toBe('analyze');
    expect(parseHash('#evaluation', true)).toBe('evaluation');
    expect(parseHash('#audit', true)).toBe('audit');
  });
});

describe('header title', () => {
  it('keeps the full app name for assistive tech and as a tooltip', () => {
    render(<Layout currentPage="analyze" onNavigate={() => {}}>content</Layout>);
    const heading = screen.getByRole('heading', { level: 1 });
    expect(heading).toHaveAccessibleName('Adaptive Trust-Aware Medical RAG');
    expect(heading).toHaveAttribute('title', 'Adaptive Trust-Aware Medical RAG');
    expect(heading).toHaveTextContent('Medical RAG');
  });
});
