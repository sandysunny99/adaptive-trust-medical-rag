/**
 * Export analysis results as Markdown or JSON.
 * Patient context is excluded by default for privacy.
 */

import type { HistoryEntry } from './historyDb';
import { RESEARCH_DISCLAIMER, disclaimerFor } from '../constants/disclaimer';

/**
 * Answer-payload fields that echo the patient context the user typed. The SSE
 * answer carries `patient_context_used` alongside `patient_context`, so both
 * must go; checked against a synthetic run that echoed nothing elsewhere.
 */
const PATIENT_INPUT_FIELDS = ['patient_context', 'patient_context_used'] as const;

export function exportAsJson(entry: HistoryEntry, includePatientContext = false): string {
  const data: Record<string, unknown> = { ...entry.result };
  if (!includePatientContext) {
    for (const field of PATIENT_INPUT_FIELDS) delete data[field];
  }
  return JSON.stringify(data, null, 2);
}

export function exportAsMarkdown(entry: HistoryEntry, _includePatientContext = false): string {
  const r = entry.result;
  const lines: string[] = [
    '# Medical RAG Analysis Report',
    '',
    `> ⚠️ ${RESEARCH_DISCLAIMER}`,
    '',
    `**Date:** ${entry.timestamp}`,
    `**Input Mode:** ${entry.inputMode}`,
    `**Gate Decision:** ${r.gate_decision || 'N/A'}`,
    '',
    '## Medications Analyzed',
    '',
  ];

  for (const med of r.medications || []) {
    lines.push(`- **${med.canonical_name || med.raw_text}**${med.rxcui ? ` (RxCUI: ${med.rxcui})` : ''} — Status: ${med.status}`);
  }

  if ((r.interactions || []).length > 0) {
    lines.push('', '## Drug-Drug Interactions', '');
    for (const ix of r.interactions) {
      lines.push(`- **${ix.drug_a} ↔ ${ix.drug_b}**: ${ix.interaction_detected ? '⚠ VERIFIED' : 'No verified evidence'}${ix.potential_effect ? ` — ${ix.potential_effect}` : ''}`);
    }
  }

  if ((r.food_guidance || []).length > 0) {
    lines.push('', '## Food & Administration', '');
    for (const fg of r.food_guidance) {
      lines.push(`- **${fg.drug}**: ${fg.food_relationship.replace(/_/g, ' ')}${fg.administration ? ` — ${fg.administration}` : ''}`);
    }
  }

  if (r.conclusion) {
    lines.push('', '## Conclusion', '', r.conclusion);
  }

  if ((r.evidence || []).length > 0) {
    lines.push('', '## Evidence Sources', '');
    for (const [i, ev] of r.evidence.entries()) {
      const link = ev.source_link_status && ev.source_link_status !== 'VERIFIED' ? ` — not a verified link: ${ev.source_link_note ?? ev.source_link_status}` : '';
      lines.push(`${i + 1}. **${ev.source_name}** — Trust: ${ev.trust_score?.toFixed(2) || 'N/A'}, Authority: ${ev.source_authority?.toFixed(2) || 'N/A'}${ev.pmid ? ` (PMID: ${ev.pmid})` : ''}${link}`);
    }
  }

  lines.push('', '---', '', disclaimerFor(r.disclaimer));
  return lines.join('\n');
}

export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}
