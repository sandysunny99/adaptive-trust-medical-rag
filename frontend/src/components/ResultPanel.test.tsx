import { describe, it, expect } from 'vitest';
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import { ResultPanel } from './ResultPanel';
import { RESEARCH_DISCLAIMER } from '../constants/disclaimer';
import type { AnalysisResult, EvidenceItem } from '../types';

// Synthetic fixture only; no patient data.
function evidence(document_id: string, text: string): EvidenceItem {
  return {
    chunk_id: `${document_id}-chunk`,
    document_id,
    source_type: 'DAILYMED',
    source_name: `https://example.test/${document_id}`,
    title: 'Evidence',
    text,
    source_authority: 0.95,
    trust_score: 0.9,
    freshness: 0.9,
    retrieval_method: 'hybrid-rrf',
    provenance_status: 'RETRIEVED',
  };
}

function makeResult(overrides: Partial<AnalysisResult> = {}): AnalysisResult {
  return {
    request_id: 'test',
    input_mode: 'direct_drugs',
    medications: [],
    patient_context: null,
    interactions: [],
    adverse_reactions: [],
    warnings: [],
    food_guidance: [],
    patient_considerations: [],
    trust: {
      overall_score: 0.9375,
      threshold: 0.3,
      risk_class: 'R0',
      is_eligible: true,
      factors: {
        source_authority: null, query_relevance: null, evidence_quality: null, freshness: null,
        consistency: null, entity_match: null, population_match: null, anti_poisoning: null, anti_injection: null,
      },
      missing_factors: [],
    },
    security: { injection_status: 'ALLOW', poisoning_status: 'ALLOW', injection_markers: [], poisoning_reason: null },
    claims: [],
    evidence: [],
    provenance: [],
    conclusion: 'Synthetic conclusion.',
    gate_decision: 'release',
    abstention_reason: null,
    disclaimer: '',
    ...overrides,
  };
}

describe('ResultPanel disclaimer', () => {
  it('renders the fixed fallback disclaimer when result.disclaimer is empty', () => {
    render(<ResultPanel result={makeResult({ disclaimer: '' })} />);
    expect(screen.getByRole('note', { name: 'Research disclaimer' })).toHaveTextContent(RESEARCH_DISCLAIMER);
  });

  it('renders the fallback when the disclaimer field is missing entirely', () => {
    const result = makeResult();
    delete (result as Partial<AnalysisResult>).disclaimer;
    render(<ResultPanel result={result} />);
    expect(screen.getByRole('note', { name: 'Research disclaimer' })).toHaveTextContent(RESEARCH_DISCLAIMER);
  });

  it('prefers the backend disclaimer when one is sent', () => {
    render(<ResultPanel result={makeResult({ disclaimer: 'Backend disclaimer text.' })} />);
    expect(screen.getByRole('note', { name: 'Research disclaimer' })).toHaveTextContent('Backend disclaimer text.');
  });
});

describe('ResultPanel trust row', () => {
  it('shows the backend trust fields as returned', () => {
    render(<ResultPanel result={makeResult()} />);
    const trust = screen.getByRole('region', { name: 'Evidence Trust' });
    expect(within(trust).getByText('0.94')).toBeInTheDocument();
    expect(within(trust).getByText('0.30')).toBeInTheDocument();
    expect(within(trust).getByText('R0')).toBeInTheDocument();
  });

  it('says "Not available" for missing trust fields', () => {
    render(<ResultPanel result={makeResult({ trust: null })} />);
    const trust = screen.getByRole('region', { name: 'Evidence Trust' });
    expect(within(trust).getAllByText('Not available')).toHaveLength(3);
  });
});

describe('ResultPanel evidence and security sections', () => {
  const items = [
    evidence('SPL-METFORMIN-001', 'Metformin text'),
    evidence('SPL-WARFARIN-001', 'Warfarin text'),
    evidence('SPL-ATORVASTATIN-005', 'Atorvastatin text'),
  ];

  it('lists every evidence item in backend order with its document tag', () => {
    render(<ResultPanel result={makeResult({ evidence: items })} />);
    expect(screen.getByRole('button', { name: /Evidence & Sources \(3\)/ })).toHaveAttribute('aria-expanded', 'true');
    const tags = screen.getAllByText(/^Document: /).map(el => el.textContent);
    expect(tags).toEqual([
      'Document: SPL-METFORMIN-001',
      'Document: SPL-WARFARIN-001',
      'Document: SPL-ATORVASTATIN-005',
    ]);
    expect(screen.queryByText(/Verified Evidence/)).not.toBeInTheDocument();
  });

  it('shows Security Checks after the analysis completes', () => {
    render(<ResultPanel result={makeResult()} />);
    expect(screen.getByRole('button', { name: /Security Checks/ })).toBeInTheDocument();
    expect(screen.getByText('Prompt Injection')).toBeInTheDocument();
  });

  it('hides Evidence & Sources and Security Checks while the analysis is running', () => {
    render(<ResultPanel result={makeResult({ evidence: items })} showDetails={false} />);
    expect(screen.queryByRole('button', { name: /Evidence & Sources/ })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Security Checks/ })).not.toBeInTheDocument();
  });

  it('clamps long evidence text with a per-item toggle and Expand all, keeping every item', async () => {
    const long = 'Synthetic evidence sentence. '.repeat(12);
    const many = Array.from({ length: 14 }, (_, i) => evidence(`DOC-${i + 1}`, i === 0 ? long : `Short text ${i + 1}`));
    render(<ResultPanel result={makeResult({ evidence: many })} />);

    expect(screen.getAllByText(/^Document: /)).toHaveLength(14);
    expect(screen.getByRole('button', { name: /Evidence & Sources \(14\)/ })).toBeInTheDocument();

    const more = screen.getByRole('button', { name: 'Show more of source 1' });
    expect(more).toHaveAttribute('aria-expanded', 'false');
    expect(screen.getByText(long.trim())).toHaveClass('line-clamp-3');
    await userEvent.click(more);
    expect(screen.getByRole('button', { name: 'Show less of source 1' })).toHaveAttribute('aria-expanded', 'true');
    expect(screen.getByText(long.trim())).not.toHaveClass('line-clamp-3');

    await userEvent.click(screen.getByRole('button', { name: 'Expand all' }));
    for (let i = 2; i <= 14; i++) expect(screen.getByText(`Short text ${i}`)).not.toHaveClass('line-clamp-3');
    await userEvent.click(screen.getByRole('button', { name: 'Collapse all' }));
    expect(screen.getByText('Short text 2')).toHaveClass('line-clamp-3');
  });

  it('shows security checks as rows with visible status text', () => {
    render(<ResultPanel result={makeResult()} />);
    const rows = screen.getAllByRole('listitem').filter(li => /Prompt Injection|Retrieval Poisoning|Evidence Integrity/.test(li.textContent ?? ''));
    expect(rows).toHaveLength(3);
    for (const row of rows) expect(row).toHaveTextContent('ALLOW');
  });

  it('marks checks that never ran as NOT RUN instead of pending or flagged', () => {
    // A run that stopped at retrieval: no security result and no trust score.
    render(<ResultPanel result={makeResult({ security: undefined, trust: undefined } as unknown as Partial<AnalysisResult>)} />);
    const rows = screen.getAllByRole('listitem').filter(li => /Prompt Injection|Retrieval Poisoning|Evidence Integrity/.test(li.textContent ?? ''));
    expect(rows).toHaveLength(3);
    for (const row of rows) {
      expect(row).toHaveTextContent('NOT RUN');
      expect(row).toHaveTextContent('The analysis stopped before this check ran.');
      expect(row).not.toHaveTextContent(/FLAG|PENDING/);
    }
  });

  it('flags evidence integrity only when the scored evidence was ineligible', () => {
    const scored = makeResult();
    render(<ResultPanel result={{ ...scored, trust: { ...scored.trust!, overall_score: 0.2, is_eligible: false } }} />);
    const row = screen.getAllByRole('listitem').find(li => /Evidence Integrity/.test(li.textContent ?? ''));
    expect(row).toHaveTextContent('FLAG');
  });
});

describe('ResultPanel food and diet guidance', () => {
  const LABEL = 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=00000000-0000-4000-8000-000000000002';
  const food = {
    drug: 'Lisinopril', administration: '', food_relationship: 'SPECIFIC FOOD/DRINK INTERACTION', timing: null,
    food_interactions: ['Potassium-containing salt substitutes are a risk factor for hyperkalemia [Source 1].'],
    evidence_status: 'VERIFIED', source: '[Source 1]',
  } as unknown as AnalysisResult['food_guidance'][number];

  it('shows each food statement with a link to the exact verified source', () => {
    const verified = { ...evidence('DAILYMED-SPL-x', 'label text'), url: LABEL, source_link_status: 'VERIFIED',
      source_identity_status: 'VERIFIED', source_title: 'LISINOPRIL TABLETS' } as EvidenceItem;
    render(<ResultPanel result={makeResult({ food_guidance: [food], evidence: [verified] })} />);
    expect(screen.getByText(/salt substitutes are a risk factor/)).toBeInTheDocument();
    const link = screen.getByRole('link', { name: /Source 1: LISINOPRIL TABLETS/ });
    expect(link).toHaveAttribute('href', LABEL);
    expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  });

  it('never links a cited source that is not verified', () => {
    render(<ResultPanel result={makeResult({ food_guidance: [food], evidence: [evidence('SPL-PLACEHOLDER', 'x')] })} />);
    expect(screen.queryByRole('link', { name: /Source 1/ })).not.toBeInTheDocument();
    expect(screen.getByText('Source 1: not a verified link')).toBeInTheDocument();
  });

  it('says no food guidance was verified, and that this is not a finding of safety', () => {
    render(<ResultPanel result={makeResult({ gate_decision: 'abstain' })} />);
    expect(screen.getByText(/No food or dietary guidance could be verified/)).toHaveTextContent(
      'This does not mean there are no food or dietary issues');
  });
});


describe('ResultPanel withheld-claim reasons', () => {
  type Claim = AnalysisResult['claims'][number];
  const claim = (strength_code?: string, strength_details?: string[], extra: Record<string, unknown> = {}): Claim => ({
    claim_id: 0, text: 'Synthetic withheld statement [Source 1].', support_state: 'UNSUPPORTED', entailment: 0.9,
    contradiction: 0, citation_present: true, citation_resolves: true, best_evidence_chunk: null,
    canonical_identity_status: null, ...(strength_code ? { strength_code } : {}),
    ...(strength_details ? { strength_details } : {}), ...extra,
  } as Claim);
  const abstain = (claims: Claim[], reason = '1 of 1 generated claims failed post-generation verification.') =>
    makeResult({ gate_decision: 'abstain', abstention_reason: reason, claims });
  const status = () => screen.getByText('The system abstained from answering.').closest('[role="status"]') as HTMLElement;

  it.each([
    ['ACTION_TOO_STRONG', ['AVOID'], /worded more strongly than the reviewed wording of its source supports/],
    ['UNSUPPORTED_DETAIL', ['QUANTITY', 'TIMING'], /added an amount or frequency and a timing that its source's reviewed wording does not state/],
    ['NO_REVIEWED_RELATIONSHIP_WORDING', [], /No reviewed statement is available for this medication relationship/],
    ['NO_REVIEWED_FOOD_WORDING', [], /No reviewed statement is available for this food or drink guidance/],
    ['A_CODE_FROM_A_LATER_BACKEND', ['RAW_INTERNAL'], /could not be verified against its source's reviewed wording/],
  ])('explains %s in plain words, inside the one abstention status', (code, details, message) => {
    render(<ResultPanel result={abstain([claim(code, details)])} />);
    expect(within(status()).getByText(message)).toBeInTheDocument();
    expect(within(status()).getByText(/does not mean the medicines are safe together/)).toBeInTheDocument();
    expect(screen.queryByText(/A_CODE_FROM|RAW_INTERNAL|AVOID|level \d/)).not.toBeInTheDocument();  // no internals
    expect(screen.queryByText(/Synthetic withheld statement/)).not.toBeInTheDocument();  // never the withheld claim
  });

  it.each([
    ['no eligible evidence', '2 evidence chunk(s) about these medications passed security checks, but none was eligible: each needs a trust score of at least 0.75 for risk tier R3 and a source authority of at least 0.30 (best trust score 0.41).', []],
    ['an unverified source identity', '1 evidence chunk(s) about these medications were retrieved, but none has a verified source identity (placeholder, shared or unverified source links), so none can be used as evidence. This is a limit of the evidence corpus, not a finding that the medications are safe together. No trust score was computed, because no evidence reached scoring.', []],
    ['no approved relationship record', '1 of 1 generated claims failed post-generation verification. 1 of them did not match an approved relationship record (a different drug pair, relation or direction, or no drug pair named).', [claim(undefined, undefined, { canonical_identity_status: 'MISMATCH' })]],
    ['a verification failure', 'Claim verification failed with an error, so the answer was not verified.', [claim(undefined, undefined, { verification_error: 'RuntimeError' })]],
  ])('keeps %s apart from a wording reason', (_, reason, claims) => {
    render(<ResultPanel result={abstain(claims as Claim[], reason)} />);
    expect(within(status()).getByText(reason)).toBeInTheDocument();
    expect(screen.queryByText(/Why claims were withheld at their wording/)).not.toBeInTheDocument();
  });

  it('names each reason once, and none for a released answer', () => {
    const { unmount } = render(<ResultPanel result={abstain([claim('ACTION_TOO_STRONG'), claim('ACTION_TOO_STRONG'),
      claim('NO_REVIEWED_FOOD_WORDING')])} />);
    expect(within(status()).getAllByRole('listitem')).toHaveLength(2);
    unmount();
    render(<ResultPanel result={makeResult({ claims: [claim('ACTION_TOO_STRONG')] })} />);
    expect(screen.queryByText(/Why claims were withheld/)).not.toBeInTheDocument();
  });
});
