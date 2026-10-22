import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { EvidenceList, ExcludedSourceList } from './EvidenceList';
import type { EvidenceItem, ExcludedSource } from '../../types';

// Synthetic fixtures only; no patient data. The set ID is a made-up example, not a real label.
const LABEL = 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=00000000-0000-4000-8000-000000000001';

function item(overrides: Partial<EvidenceItem> = {}): EvidenceItem {
  return {
    chunk_id: 'c1',
    document_id: 'SPL-SYNTHETIC-001',
    source_type: 'DAILYMED',
    source_name: LABEL,
    url: LABEL,
    source_link_status: 'VERIFIED',
    source_link_note: 'Verified link to the original document.',
    source_identity_status: 'VERIFIED',
    source_title: 'Synthetic label title',
    external_id: '00000000-0000-4000-8000-000000000001',
    source_version: '3',
    title: 'Evidence [Source 1]',
    text: 'Synthetic evidence text.',
    source_authority: 0.95,
    trust_score: 0.9,
    freshness: 0.9,
    retrieval_method: 'hybrid-rrf',
    provenance_status: 'CONTENT_HASH_MATCHED',
    claim_support_status: 'SUPPORTS_VERIFIED_CLAIM',
    ...overrides,
  };
}

describe('EvidenceList source identity', () => {
  it('shows a verified source with its title, external ID, version and link', () => {
    render(<EvidenceList evidence={[item()]} />);
    expect(screen.getByText('Source verified')).toBeInTheDocument();
    expect(screen.getByText('Supports a verified claim')).toBeInTheDocument();
    expect(screen.getByText(/Synthetic label title/)).toBeInTheDocument();
    expect(screen.getByText('00000000-0000-4000-8000-000000000001')).toBeInTheDocument();
    expect(screen.getByText(/version 3/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: LABEL })).toHaveAttribute('href', LABEL);
  });

  it('never links a rejected source, even when a URL is present', () => {
    render(<EvidenceList evidence={[item({
      source_identity_status: 'REJECTED_SOURCE_IDENTITY', claim_support_status: 'NO_VERIFIED_CLAIM',
    })]} />);
    expect(screen.getByText('Source rejected')).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
    expect(screen.queryByText('Source verified')).not.toBeInTheDocument();
  });

  it('never links a mismatched identifier that the backend did not verify', () => {
    // An https URL alone is not verification: the link status from the backend decides.
    render(<EvidenceList evidence={[item({ source_link_status: 'SHARED', source_identity_status: 'UNVERIFIED' })]} />);
    expect(screen.getByText('Source not verified')).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });

  it('shows partial verification: a verified source that supports no verified claim', () => {
    render(<EvidenceList evidence={[
      item(),
      item({ chunk_id: 'c2', claim_support_status: 'NO_VERIFIED_CLAIM', text: 'Second synthetic text.' }),
    ]} />);
    expect(screen.getByText('Supports a verified claim')).toBeInTheDocument();
    expect(screen.getByText('Supports no verified claim')).toBeInTheDocument();
  });

  it('treats an item without an identity status as not verified', () => {
    render(<EvidenceList evidence={[item({ source_identity_status: undefined })]} />);
    expect(screen.getByText('Source not verified')).toBeInTheDocument();
  });

  it('says the scores are heuristics that never replace the identity and claim checks', () => {
    render(<EvidenceList evidence={[item()]} />);
    expect(screen.getByText(/not calibrated probabilities/)).toBeInTheDocument();
    expect(screen.getByText(/never replace the source-identity and claim checks/)).toBeInTheDocument();
  });
});

describe('ExcludedSourceList', () => {
  it('names each excluded source, its status and the reason, without linking it', () => {
    const sources: ExcludedSource[] = [{
      chunk_id: 'c9', document_id: 'SPL-PLACEHOLDER-9', source_type: 'DAILYMED',
      source_name: 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-placeholder',
      source_link_status: 'PLACEHOLDER', source_identity_status: 'REJECTED_SOURCE_IDENTITY',
      reason: 'Placeholder link; it does not identify the original document.',
    }];
    render(<ExcludedSourceList sources={sources} />);
    expect(screen.getByText('Source rejected')).toBeInTheDocument();
    expect(screen.getByText('Document: SPL-PLACEHOLDER-9')).toBeInTheDocument();
    expect(screen.getByText(/does not identify the original document/)).toBeInTheDocument();
    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});
