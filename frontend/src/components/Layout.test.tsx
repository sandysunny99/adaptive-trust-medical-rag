import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { Layout } from './Layout';

// Round 6: drug names come from RxNorm (NLM); the RxNav terms of service ask for this attribution statement.
describe('Layout footer', () => {
  it('carries the NLM data attribution', () => {
    render(<Layout currentPage="analyze" onNavigate={() => {}}><p>content</p></Layout>);
    expect(screen.getByRole('contentinfo')).toHaveTextContent(
      'This product uses publicly available data from the U.S. National Library of Medicine (NLM).');
  });
});
