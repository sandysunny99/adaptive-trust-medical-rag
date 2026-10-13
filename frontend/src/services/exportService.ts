import type { AnalysisResult } from '../types';

export interface ExportOptions {
  includeUserContext?: boolean;
}

function exportableResult(result: AnalysisResult, options: ExportOptions = {}): Record<string, unknown> {
  const copy = JSON.parse(JSON.stringify(result)) as Record<string, unknown>;
  if (!options.includeUserContext) {
    delete copy.patient_context;
    delete copy.additional_instructions;
  }
  return copy;
}

function formatValue(value: unknown): string {
  if (value === null || value === undefined || value === '') return 'Unavailable';
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}

export function buildJsonExport(result: AnalysisResult, options?: ExportOptions): string {
  return JSON.stringify({
    export_version: 1,
    exported_at: new Date().toISOString(),
    disclaimer: result.disclaimer,
    analysis: exportableResult(result, options),
  }, null, 2);
}

export function buildMarkdownExport(result: AnalysisResult, options?: ExportOptions): string {
  const safe = exportableResult(result, options);
  const medications = result.medications.length
    ? result.medications.map(m => `- ${m.canonical_name || m.raw_text} (RxCUI: ${formatValue(m.rxcui)})`).join('\n')
    : '- Unavailable';
  const evidence = result.evidence.length
    ? result.evidence.map((item, index) =>
      `### ${index + 1}. ${item.source_name || 'Unnamed source'}\n${item.text || 'Excerpt unavailable'}\n\n` +
      `- PMID: ${formatValue(item.pmid)}\n- DOI: ${formatValue(item.doi)}\n- Trust: ${formatValue(item.trust_score)}\n- Provenance: ${formatValue(item.provenance_status)}`,
    ).join('\n\n')
    : 'Unavailable';
  const claims = result.claims.length
    ? result.claims.map(claim => `- **${claim.support_state}**: ${claim.text}`).join('\n')
    : 'Unavailable';

  return [
    '# Medical RAG Research Report',
    '',
    `Exported: ${new Date().toISOString()}`,
    `Status: ${result.gate_decision}`,
    '',
    `> ${result.disclaimer}`,
    '',
    '## Medications',
    medications,
    '',
    '## Conclusion',
    result.conclusion || 'Unavailable',
    '',
    '## Evidence',
    evidence,
    '',
    '## Claim verification',
    claims,
    '',
    '## Trust and security',
    `Trust: ${formatValue(result.trust)}`,
    `Security: ${formatValue(result.security)}`,
    `Warnings: ${result.warnings.length ? result.warnings.join('; ') : 'None reported'}`,
    '',
    '## Abstention and unavailable information',
    result.abstention_reason || 'No abstention reason reported.',
    '',
    `Provider/model: ${formatValue(result.used_model)}`,
    options?.includeUserContext ? `\nUser-supplied context included by explicit choice: ${formatValue(safe.patient_context)}` : '',
  ].join('\n');
}

export function sanitizeFilename(value: string): string {
  return value.replace(/[^a-z0-9._-]+/gi, '-').replace(/^-+|-+$/g, '').slice(0, 80) || 'medical-rag-report';
}

export function downloadText(content: string, filename: string, mimeType: string): void {
  const url = URL.createObjectURL(new Blob([content], { type: mimeType }));
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = sanitizeFilename(filename);
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 0);
}

export function downloadJson(result: AnalysisResult, options?: ExportOptions): void {
  downloadText(buildJsonExport(result, options), 'medical-rag-report.json', 'application/json');
}

export function downloadMarkdown(result: AnalysisResult, options?: ExportOptions): void {
  downloadText(buildMarkdownExport(result, options), 'medical-rag-report.md', 'text/markdown');
}
