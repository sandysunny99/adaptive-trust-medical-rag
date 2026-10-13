import { describe, expect, it } from 'vitest';
import {
  buildJsonExport, buildMarkdownExport, sanitizeFilename,
} from './exportService';
import { createHistoryRecord } from './historyDb';
import type { AnalysisResult } from '../types';

const result: AnalysisResult = {
  request_id: 'request-1',
  input_mode: 'direct_drugs',
  medications: [{
    raw_text: 'Warfarin',
    canonical_name: 'warfarin',
    rxcui: '11289',
    brand_name: null,
    formulation: null,
    strength: null,
    frequency: null,
    route: null,
    confidence: 1,
    source: 'rxnorm_exact',
    status: 'MATCHED',
  }],
  patient_context: { known_allergies: ['SYNTHETIC_CONTEXT_MARKER'] },
  additional_instructions: 'SYNTHETIC_INSTRUCTIONS_MARKER',
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
  conclusion: 'Evidence is unavailable.',
  gate_decision: 'abstain',
  abstention_reason: 'Insufficient evidence.',
  disclaimer: 'Research prototype only.',
};

describe('exportService', () => {
  it('omits user context and instructions by default', () => {
    const output = buildJsonExport(result);
    expect(output).not.toContain('SYNTHETIC_CONTEXT_MARKER');
    expect(output).not.toContain('SYNTHETIC_INSTRUCTIONS_MARKER');
    expect(output).toContain('"rxcui": "11289"');
  });

  it('includes user context only after explicit opt-in', () => {
    const output = buildMarkdownExport(result, { includeUserContext: true });
    expect(output).toContain('SYNTHETIC_CONTEXT_MARKER');
  });

  it('does not invent evidence or a successful status', () => {
    const output = buildMarkdownExport(result);
    expect(output).toContain('Status: abstain');
    expect(output).toContain('Unavailable');
    expect(output).not.toContain('Verified Evidence');
  });

  it('sanitizes download filenames', () => {
    expect(sanitizeFilename('../unsafe report?.md')).toBe('..-unsafe-report-.md');
  });

  it('creates a browser-local record without the original image', () => {
    const record = createHistoryRecord(result);
    expect(record.requestId).toBe('request-1');
    expect(record.status).toBe('abstained');
    expect(record).not.toHaveProperty('image');
  });
});
