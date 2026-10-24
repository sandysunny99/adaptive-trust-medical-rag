import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { MedicationCard } from '../MedicationCard';
import { TrustSummary } from './TrustSummary';
import { EvidenceList } from './EvidenceList';
import { safeEvidenceUrl } from '../../services/evidenceDisplay';
import type { EvidenceItem, MedicationInfo, TrustInfo } from '../../types';

const LABEL = 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=00000000-0000-4000-8000-000000000002';

function med(over: Partial<MedicationInfo>): MedicationInfo {
  return { raw_text: 'Lisinopril', canonical_name: 'lisinopril', rxcui: '29046', status: 'MATCHED',
           source: 'cache', ...over } as MedicationInfo;
}

describe('medication identity is not evidence verification', () => {
  it('says "Identity resolved", never "Verified", and names the method', () => {
    render(<MedicationCard medication={med({ identity_method: 'seed_cache' })} />);
    expect(screen.getByText('Identity resolved')).toBeInTheDocument();
    expect(screen.queryByText('Verified')).not.toBeInTheDocument();
    expect(screen.getByText(/Curated local mapping/)).toBeInTheDocument();
    expect(screen.getByText(/Drug identity only/)).toBeInTheDocument();
  });

  it('keeps a cached approximate match marked as approximate', () => {
    render(<MedicationCard medication={med({ identity_method: 'rxnorm_approx' })} />);
    expect(screen.getByText(/RxNorm approximate match \(cached\)/)).toBeInTheDocument();
  });

  it('names an exact RxNorm match', () => {
    render(<MedicationCard medication={med({ raw_text: 'Spironolactone', source: 'rxnorm_exact',
                                             identity_method: 'rxnorm_exact' })} />);
    expect(screen.getByText(/RxNorm exact match/)).toBeInTheDocument();
  });
});

describe('a trust score that was never computed', () => {
  it('reads "Not computed", not 0.00', () => {
    const trust = { overall_score: null, score_status: 'NO_ELIGIBLE_EVIDENCE', threshold: 0.6, risk_class: 'R2',
                    is_eligible: false, factors: {}, missing_factors: [] } as unknown as TrustInfo;
    render(<TrustSummary trust={trust} />);
    expect(screen.getByText('Not computed (no eligible evidence)')).toBeInTheDocument();
    expect(screen.queryByText('0.00')).not.toBeInTheDocument();
  });
});

describe('citation links', () => {
  it.each([
    ['javascript:alert(1)'], ['data:text/html,hi'], ['file:///etc/passwd'], ['http://dailymed.nlm.nih.gov/x'],
    ['https://evil.example/dailymed'], ['https://dailymed.nlm.nih.gov.evil.example/x'],
    ['https://user:pw@dailymed.nlm.nih.gov/x'], ['not a url'],
    ['https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=example-lisinopril'],
  ])('rejects %s', (url) => {
    expect(safeEvidenceUrl(url)).toBeUndefined();
  });

  it('accepts the exact verified DailyMed label and PubMed record', () => {
    expect(safeEvidenceUrl(LABEL)).toBe(LABEL);
    expect(safeEvidenceUrl('https://pubmed.ncbi.nlm.nih.gov/12345678/')).toBe('https://pubmed.ncbi.nlm.nih.gov/12345678/');
  });

  it('links a verified source to its exact URL in a new tab, and nothing else', () => {
    const base = { document_id: 'd', source_type: 'DAILYMED', title: 't', text: 'x', source_authority: 0.95,
                   trust_score: 0.8, freshness: 0.9, retrieval_method: 'hybrid-rrf', provenance_status: 'CONTENT_HASH_MATCHED' };
    const evidence = [
      { ...base, chunk_id: 'ok', source_name: LABEL, url: LABEL, source_link_status: 'VERIFIED', source_identity_status: 'VERIFIED' },
      { ...base, chunk_id: 'host', source_name: 'x', url: 'https://evil.example/a', source_link_status: 'VERIFIED',
        source_identity_status: 'VERIFIED' },
      { ...base, chunk_id: 'pending', source_name: LABEL, url: LABEL, source_link_status: 'UNVERIFIED',
        source_identity_status: 'UNVERIFIED' },
    ] as EvidenceItem[];
    render(<EvidenceList evidence={evidence} />);
    const links = screen.getAllByRole('link');
    expect(new Set(links.map(l => l.getAttribute('href')))).toEqual(new Set([LABEL]));
    for (const link of links) {
      expect(link).toHaveAttribute('target', '_blank');
      expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    }
  });
});
