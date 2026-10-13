/**
 * The one research disclaimer used across the UI: header badge tooltip,
 * analysis results (when the backend sends none) and the About page.
 *
 * Text matches the backend schema default (AnalyzeResponse.disclaimer in
 * src/adaptive_trust_medical_rag/api/live_schemas.py). The SSE `answer`
 * payload currently omits that field, so the frontend must not rely on it.
 */
export const RESEARCH_DISCLAIMER =
  'RESEARCH OUTPUT ONLY. Not reviewed by clinicians. Not for clinical use. ' +
  'Evidence-grounded response from a research testbed.';

/** Use the backend's disclaimer when present, otherwise the fixed constant. */
export function disclaimerFor(backendText: string | null | undefined): string {
  const text = backendText?.trim();
  return text ? text : RESEARCH_DISCLAIMER;
}
