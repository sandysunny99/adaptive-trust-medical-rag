import { describe, it, expect } from 'vitest';
import { exportAsJson, exportAsMarkdown } from './exportService';
import type { HistoryEntry } from './historyDb';
import type { AnalysisResult } from '../types';

// Synthetic markers only; no real patient data.
const MARKERS = [
  'SYNTHETIC-CONDITION-TEST',
  'SYNTHETIC-ALLERGY-TEST',
  'SYNTHETIC-MED-TEST',
];

const patientContext = {
  age: 60,
  sex: 'other' as const,
  known_allergies: ['SYNTHETIC-ALLERGY-TEST'],
  known_conditions: ['SYNTHETIC-CONDITION-TEST'],
  current_medications: ['SYNTHETIC-MED-TEST'],
};

function entry(): HistoryEntry {
  // Shaped like the live SSE `answer` payload, which echoes the input as
  // `patient_context_used` (not in the AnalysisResult type).
  const result = {
    request_id: 'synthetic',
    input_mode: 'direct_drugs',
    medications: [{
      raw_text: 'Metformin', canonical_name: 'metformin', rxcui: '6809', brand_name: null,
      formulation: null, strength: null, frequency: null, route: null, confidence: 1,
      source: 'cache', status: 'MATCHED',
    }],
    patient_context: patientContext,
    patient_context_used: { ...patientContext, pregnancy_status: null },
    interactions: [],
    adverse_reactions: [],
    warnings: [],
    food_guidance: [],
    patient_considerations: [],
    trust: null,
    security: null,
    claims: [],
    evidence: [],
    provenance: [],
    conclusion: 'Synthetic conclusion.',
    gate_decision: 'release',
    abstention_reason: null,
    disclaimer: '',
  } as unknown as AnalysisResult;

  return {
    id: 'synthetic-entry',
    timestamp: '2026-10-13T00:00:00.000Z',
    drugNames: ['metformin'],
    inputMode: 'direct_drugs',
    gateDecision: 'release',
    result,
  };
}

describe('exports leave patient context out', () => {
  it('JSON export contains no patient input', () => {
    const json = exportAsJson(entry());
    for (const marker of MARKERS) expect(json).not.toContain(marker);
    const parsed = JSON.parse(json);
    expect(parsed).not.toHaveProperty('patient_context');
    expect(parsed).not.toHaveProperty('patient_context_used');
    expect(parsed.conclusion).toBe('Synthetic conclusion.');
  });

  it('Markdown export contains no patient input', () => {
    const md = exportAsMarkdown(entry());
    for (const marker of MARKERS) expect(md).not.toContain(marker);
    expect(md).toContain('Synthetic conclusion.');
  });

  it('does not mutate the stored entry', () => {
    const e = entry();
    exportAsJson(e);
    expect(JSON.stringify(e.result)).toContain('SYNTHETIC-CONDITION-TEST');
  });
});
