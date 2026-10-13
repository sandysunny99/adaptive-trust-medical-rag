import { ExternalLink } from 'lucide-react';
import type { EvidenceItem } from '../../types';

/**
 * Evidence items exactly as the backend returned them: same order, nothing
 * filtered, hidden or relabelled. Each item shows its document ID and source
 * type as tags so evidence about a different drug stays visible. The payload
 * has no drug/entity field, so none is inferred here.
 */
export function EvidenceList({ evidence }: { evidence: EvidenceItem[] }) {
  return (
    <ol className="divide-y divide-border">
      {evidence.map((ev, i) => (
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
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] text-foreground">
                    {ev.source_type}
                  </span>
                )}
                {ev.provenance_status && (
                  <span className="rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
                    {ev.provenance_status}
                  </span>
                )}
              </div>
              <p className="mt-1 break-all text-xs text-muted-foreground">{ev.source_name || ev.title}</p>
              <p className="mt-1 text-sm text-foreground line-clamp-3">{ev.text}</p>
              <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-[11px] text-muted-foreground">
                {ev.pmid && <span>PMID: {ev.pmid}</span>}
                {ev.doi && <span>DOI: {ev.doi}</span>}
                <span>Authority: {typeof ev.source_authority === 'number' ? ev.source_authority.toFixed(2) : 'Not available'}</span>
                <span>Trust: {typeof ev.trust_score === 'number' ? ev.trust_score.toFixed(2) : 'Not available'}</span>
                <span>Freshness: {typeof ev.freshness === 'number' ? ev.freshness.toFixed(2) : 'Not available'}</span>
                {ev.retrieval_method && <span>Method: {ev.retrieval_method}</span>}
              </div>
            </div>
            {ev.url && (
              <a
                href={ev.url}
                target="_blank"
                rel="noopener noreferrer"
                aria-label={`Open source ${i + 1} in a new tab`}
                className="shrink-0 rounded p-1.5 text-muted-foreground hover:text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <ExternalLink size={14} aria-hidden="true" />
              </a>
            )}
          </div>
        </li>
      ))}
    </ol>
  );
}
