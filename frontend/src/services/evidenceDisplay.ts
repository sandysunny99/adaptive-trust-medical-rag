/** Display rules for evidence links and trust scores, shared by the result components. */
import type { EvidenceItem, TrustInfo } from '../types';

export const NOT_AVAILABLE = 'Not available';

export function formatScore(value: unknown): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(2) : NOT_AVAILABLE;
}

export const NOT_COMPUTED = 'Not computed (no eligible evidence)';

/** The trust score, or why there is none. No eligible evidence is not a computed score of 0. */
export function trustScoreText(trust: TrustInfo | null | undefined): string {
  if (trust?.score_status === 'NO_ELIGIBLE_EVIDENCE') return NOT_COMPUTED;
  return formatScore(trust?.overall_score);
}

/** Evidence sources a citation may open; any other host is shown as text, never linked. */
const EVIDENCE_HOSTS: ReadonlySet<string> = new Set([
  'dailymed.nlm.nih.gov', 'pubmed.ncbi.nlm.nih.gov', 'www.ncbi.nlm.nih.gov', 'europepmc.org',
  'www.europepmc.org', 'open.fda.gov', 'api.fda.gov', 'clinicaltrials.gov', 'www.clinicaltrials.gov',
]);

/** The URL, if it is a well-formed https link to an evidence host and not a placeholder. */
export function safeEvidenceUrl(url?: string | null): string | undefined {
  if (!url) return undefined;
  let parsed: URL;
  try {
    parsed = new URL(url);
  } catch {
    return undefined;
  }
  if (parsed.protocol !== 'https:' || parsed.username || parsed.password) return undefined;
  if (!EVIDENCE_HOSTS.has(parsed.hostname.toLowerCase())) return undefined;
  if (/(^|&)setid=example-/i.test(parsed.search.slice(1))) return undefined;
  return parsed.href;
}


/**
 * A link only for a source the backend verified for this chunk (link and identity), at a safe
 * evidence URL; never inferred from the text. Opening it never changes its verification state.
 */
export function verifiedHref(ev: EvidenceItem): string | undefined {
  if (ev.source_link_status !== 'VERIFIED' || ev.source_identity_status === 'REJECTED_SOURCE_IDENTITY') {
    return undefined;
  }
  return safeEvidenceUrl(ev.url);
}

/** The [Source N] numbers cited in the given texts, in order, without repeats. */
export function citedSourceNumbers(...texts: (string | null | undefined)[]): number[] {
  const seen = new Set<number>();
  for (const t of texts) for (const m of (t || '').matchAll(/\[Source (\d+)\]/g)) seen.add(Number(m[1]));
  return [...seen];
}
