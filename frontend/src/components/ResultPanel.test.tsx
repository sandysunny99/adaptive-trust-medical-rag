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
  const LABEL = 'https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid=34ebeea1-6812-4697-84c4-b2ae4f39e55f';
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

// 2026-10-26 audit round 2: food outcomes are named, and a withheld answer lists which statements failed.
describe('ResultPanel food status and claim list', () => {
  it.each([
    ['NOT_RUN', 'was not assessed'],
    ['NONE_FOUND', 'contains no food or dietary guidance'],
    ['NOT_VERIFIED', 'could not be verified against the sources'],
    ['WITHHELD', 'The answer was withheld'],
  ] as const)('explains %s instead of one generic message', (status, text) => {
    render(<ResultPanel result={makeResult({ food_guidance_status: status, gate_decision: 'abstain' })} />);
    expect(screen.getByText(new RegExp(text))).toBeInTheDocument();
    expect(screen.getByText(/does not mean there are no food or dietary issues/)).toBeInTheDocument();
  });

  it('lists each statement with its verification result and why it failed', () => {
    render(<ResultPanel result={makeResult({
      gate_decision: 'abstain',
      claims: [
        { claim_id: 0, field: 'conclusion', text: 'Lisinopril can cause hyperkalemia [Source 1].', support_state: 'SUPPORTED',
          entailment: 0.99, contradiction: 0, citation_present: true, citation_resolves: true,
          best_evidence_chunk: null, canonical_identity_status: null },
        { claim_id: 1, field: 'warnings', text: 'Avoid all diuretics.', support_state: 'UNSUPPORTED',
          entailment: 0.9, contradiction: 0, citation_present: false, citation_resolves: false,
          best_evidence_chunk: null, canonical_identity_status: null },
      ],
    })} />);
    expect(screen.getByText('Claim verification (1 of 2 verified)')).toBeInTheDocument();
    expect(screen.getByText('Avoid all diuretics.')).toBeInTheDocument();
    expect(screen.getByText('Cites no source')).toBeInTheDocument();
  });
});
