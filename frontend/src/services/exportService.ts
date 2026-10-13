/**
 * Export analysis results as Markdown or JSON.
 * Patient context is excluded by default for privacy.
 */

import type { HistoryEntry } from './historyDb';

export function exportAsJson(entry: HistoryEntry, includePatientContext = false): string {
  const data = { ...entry.result };
  if (!includePatientContext) {
    data.patient_context = null;
  }
  return JSON.stringify(data, null, 2);
}

export function exportAsMarkdown(entry: HistoryEntry, _includePatientContext = false): string {
  const r = entry.result;
  const lines: string[] = [
    '# Medical RAG Analysis Report',
    '',
    '> ⚠️ RESEARCH OUTPUT ONLY. Not reviewed by clinicians. Not for clinical use.',
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
      lines.push(`${i + 1}. **${ev.source_name}** — Trust: ${ev.trust_score?.toFixed(2) || 'N/A'}, Authority: ${ev.source_authority?.toFixed(2) || 'N/A'}${ev.pmid ? ` (PMID: ${ev.pmid})` : ''}`);
    }
  }

  lines.push('', '---', '', r.disclaimer || 'RESEARCH OUTPUT ONLY. Not for clinical use.');
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
