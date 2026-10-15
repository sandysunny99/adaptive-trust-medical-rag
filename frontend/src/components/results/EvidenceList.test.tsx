import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EvidenceList } from './EvidenceList';
import type { EvidenceItem } from '../../types';

// Synthetic fixture only; no patient data.
const LABEL = 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=9aaffb41-408c-4372-8fd5-1d649450c0e9';
const PLACEHOLDER = 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-simvastatin';

function item(overrides: Partial<EvidenceItem> = {}): EvidenceItem {
  return {
    chunk_id: 'c1',
    document_id: 'SPL-SYNTHETIC-001',
    source_type: 'DAILYMED',
    source_name: PLACEHOLDER,
    source_link_status: 'PLACEHOLDER',
    source_link_note: 'Placeholder link in the frozen corpus; it does not identify the original document.',
    title: 'Evidence [Source 1]',
    text: 'Synthetic evidence text.',
    source_authority: 0.95,
    trust_score: 0.9,
    freshness: 0.9,
    retrieval_method: 'hybrid-rrf',
    provenance_status: 'RETRIEVED',
    ...overrides,
  };
}

describe('EvidenceList source links', () => {
  it('links a verified source to the original document in a new tab', () => {
    render(<EvidenceList evidence={[item({
      source_name: LABEL, url: LABEL, source_link_status: 'VERIFIED',
      source_link_note: 'Verified link to the original document.',
    })]} />);
    const link = screen.getByRole('link', { name: LABEL });
    expect(link).toHaveAttribute('href', LABEL);
    expect(link).toHaveAttribute('target', '_blank');
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    expect(screen.getByRole('link', { name: 'Open source 1 (opens in new tab)' })).toHaveAttribute('href', LABEL);
    expect(screen.queryByText('Not linked:')).not.toBeInTheDocument();
  });

  it('shows an unverified source as text with the reason, never as a link', () => {
    render(<EvidenceList evidence={[item()]} />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.getByText(PLACEHOLDER)).toBeInTheDocument();
    expect(screen.getByText('Not linked:')).toBeInTheDocument();
    expect(screen.getByText(/does not identify the original document/)).toBeInTheDocument();
  });

  it.each(['http://dailymed.nlm.nih.gov/x', 'javascript:alert(1)'])('never links %s', url => {
    render(<EvidenceList evidence={[item({ url, source_link_status: 'VERIFIED' })]} />);
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
