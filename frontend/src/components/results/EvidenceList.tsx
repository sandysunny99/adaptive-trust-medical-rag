import { useId, useLayoutEffect, useRef, useState } from 'react';
import { Icons, SOURCE_TYPE_ICONS } from '../../ui/icons';
import type { EvidenceItem, ExcludedSource, SourceIdentityStatus } from '../../types';
import { verifiedHref } from '../../services/evidenceDisplay';

const IDENTITY_LABELS: Record<SourceIdentityStatus, { label: string; className: string }> = {
  VERIFIED: { label: 'Source verified', className: 'bg-success-soft text-success' },
  UNVERIFIED: { label: 'Source not verified', className: 'bg-warning-soft text-warning' },
  REJECTED_SOURCE_IDENTITY: { label: 'Source rejected', className: 'bg-destructive-soft text-destructive' },
};

/** The source-identity tag. An item without one predates the gate and is shown as not verified. */
function IdentityBadge({ status }: { status?: SourceIdentityStatus }) {
  const { label, className } = IDENTITY_LABELS[status ?? 'UNVERIFIED'];
  return <span className={`rounded px-1.5 py-0.5 text-[11px] font-medium ${className}`}>{label}</span>;
}

/** Chunks the backend left out before generation because their source identity is not verified. */
export function ExcludedSourceList({ sources }: { sources: ExcludedSource[] }) {
  return (
    <div>
      <p className="mb-2 text-xs text-muted-foreground">
        These retrieved records were not used as evidence: their source could not be shown to be the
        document they name. This is a limit of the evidence, not a finding about the medications.
      </p>
      <ul className="divide-y divide-border">
        {sources.map((s, i) => (
          <li key={`${s.chunk_id}-${i}`} className="py-2 text-xs">
            <div className="flex flex-wrap items-center gap-2">
              <IdentityBadge status={s.source_identity_status} />
              <span className="font-mono text-[11px] text-foreground">Document: {s.document_id}</span>
              {s.source_type && <span className="rounded bg-muted px-1.5 py-0.5 text-[11px]">{s.source_type}</span>}
            </div>
            {s.source_name && <p className="mt-1 break-all text-muted-foreground">{s.source_name}</p>}
            <p className="mt-0.5 text-muted-foreground">{s.reason}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}

function SourceTypeIcon({ sourceType }: { sourceType: string }) {
  const name = SOURCE_TYPE_ICONS[sourceType];
  if (!name) return null;
  const Icon = Icons[name];
  return <Icon size={12} />;
}

/** Text long enough that it may exceed three lines when layout can't be measured (e.g. tests). */
const LONG_TEXT_CHARS = 180;

interface EvidenceTextProps {
  id: string;
  text: string;
  index: number;
  expanded: boolean;
  onToggle: () => void;
}

/** Evidence text clamped to three lines, with a Show more / Show less toggle when it overflows. */
function EvidenceText({ id, text, index, expanded, onToggle }: EvidenceTextProps) {
  const ref = useRef<HTMLParagraphElement>(null);
  const [overflows, setOverflows] = useState(text.length > LONG_TEXT_CHARS);

  useLayoutEffect(() => {
    const el = ref.current;
    if (!el || expanded) return;
    const measure = () => {
      // jsdom reports 0 for both; keep the length-based guess there.
      if (el.clientHeight > 0) setOverflows(el.scrollHeight > el.clientHeight + 1);
    };
    measure();
    if (typeof ResizeObserver === 'undefined') return;
    const ro = new ResizeObserver(measure);
    ro.observe(el);
    return () => ro.disconnect();
  }, [expanded, text]);

  return (
    <>
      <p id={id} ref={ref} className={`mt-1 text-sm text-foreground ${expanded ? '' : 'line-clamp-3'}`}>
        {text}
      </p>
      {(overflows || expanded) && (
        <button
          type="button"
          aria-expanded={expanded}
          aria-controls={id}
          aria-label={`${expanded ? 'Show less' : 'Show more'} of source ${index + 1}`}
          onClick={onToggle}
          className="mt-1 rounded text-xs font-medium text-primary hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          {expanded ? 'Show less' : 'Show more'}
        </button>
      )}
    </>
  );
}

/**
 * Evidence items exactly as the backend returned them: same order, nothing
 * filtered, hidden or relabelled, every tag visible. Each item shows its
 * document ID and source type so evidence about a different drug stays
 * visible. The payload has no drug/entity field, so none is inferred here.
 * Only the body text is clamped; Expand all shows every item in full.
 */
export function EvidenceList({ evidence }: { evidence: EvidenceItem[] }) {
  const [expanded, setExpanded] = useState<Set<number>>(() => new Set());
  const baseId = useId();
  const allExpanded = evidence.length > 0 && expanded.size === evidence.length;

  const toggle = (i: number) =>
    setExpanded(prev => {
      const next = new Set(prev);
      if (next.has(i)) next.delete(i); else next.add(i);
      return next;
    });

  return (
    <div>
      <div className="mb-3 flex justify-end">
        <button
          type="button"
          onClick={() => setExpanded(allExpanded ? new Set() : new Set(evidence.map((_, i) => i)))}
          className="inline-flex items-center gap-1 rounded text-xs font-medium text-primary hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <Icons.expandAll size={14} />
          {allExpanded ? 'Collapse all' : 'Expand all'}
        </button>
      </div>
      <ol className="divide-y divide-border">
        {evidence.map((ev, i) => {
          const href = verifiedHref(ev);
          return (
            <li key={`${ev.chunk_id || 'chunk'}-${i}`} className="py-3 first:pt-0 last:pb-0">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-bold text-muted-foreground">[{i + 1}]</span>
                    {ev.document_id && (
                      <span className="rounded border border-primary/30 bg-primary-soft px-1.5 py-0.5 font-mono text-[11px] font-medium text-foreground">
                        Document: {ev.document_id}
                      </span>
                    )}
                    {ev.source_type && (
                      <span className="inline-flex items-center gap-1 rounded bg-muted px-1.5 py-0.5 text-[11px] text-foreground">
                        <SourceTypeIcon sourceType={ev.source_type} />
                        {ev.source_type}
                      </span>
                    )}
                    <IdentityBadge status={ev.source_identity_status} />
                    {ev.claim_support_status === 'SUPPORTS_VERIFIED_CLAIM' && (
                      <span className="rounded bg-success-soft px-1.5 py-0.5 text-[11px] font-medium text-success">
                        Supports a verified claim
                      </span>
                    )}
                    {ev.claim_support_status === 'NO_VERIFIED_CLAIM' && (
                      <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
                        Supports no verified claim
                      </span>
                    )}
                    {ev.provenance_status && (
                      <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
                        {ev.provenance_status}
                      </span>
                    )}
                  </div>
                  {href ? (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-1 block break-all rounded text-xs text-primary hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      {ev.source_name || href}
                    </a>
                  ) : (
                    <>
                      <p className="mt-1 break-all text-xs text-muted-foreground">{ev.source_name || ev.title}</p>
                      {ev.source_link_note && (
                        <p className="mt-0.5 text-[11px] text-muted-foreground">
                          <span className="font-medium text-foreground">Not linked:</span> {ev.source_link_note}
                        </p>
                      )}
                    </>
                  )}
                  {(ev.source_title || ev.external_id) && (
                    <p className="mt-0.5 break-words text-[11px] text-muted-foreground">
                      {ev.source_title}
                      {ev.external_id && <> · ID: <span className="font-mono">{ev.external_id}</span></>}
                      {ev.source_version && <> · version {ev.source_version}</>}
                    </p>
                  )}
                  <EvidenceText id={`${baseId}-text-${i}`} text={ev.text} index={i} expanded={expanded.has(i)} onToggle={() => toggle(i)} />
                  <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
                    {ev.pmid && <span>PMID: {ev.pmid}</span>}
                    {ev.doi && <span>DOI: {ev.doi}</span>}
                    <span>Authority: {typeof ev.source_authority === 'number' ? ev.source_authority.toFixed(2) : 'Not available'}</span>
                    <span>Trust: {typeof ev.trust_score === 'number' ? ev.trust_score.toFixed(2) : 'Not available'}</span>
                    <span>Freshness: {typeof ev.freshness === 'number' ? ev.freshness.toFixed(2) : 'Not available'}</span>
                    {ev.retrieval_method && <span>Method: {ev.retrieval_method}</span>}
                  </div>
                </div>
                {href && (
                  <a
                    href={href}
                    target="_blank"
                    rel="noopener noreferrer"
                    aria-label={`Open source ${i + 1} (opens in new tab)`}
                    title="Opens in new tab"
                    className="shrink-0 rounded p-1.5 text-muted-foreground hover:text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  >
                    <Icons.externalLink size={14} />
                  </a>
                )}
              </div>
            </li>
          );
        })}
      </ol>
      <p className="mt-3 text-[11px] text-muted-foreground">
        Authority, trust and freshness are heuristic scores from 0 to 1 used for ranking and eligibility.
        They are not calibrated probabilities, and they never replace the source-identity and claim checks.
      </p>
    </div>
  );
}
