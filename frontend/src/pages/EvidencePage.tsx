import { FileSearch, ExternalLink, Shield } from 'lucide-react';
import type { AnalysisResult } from '../types';

interface EvidencePageProps {
  latestResult?: AnalysisResult | null;
}

export function EvidencePage({ latestResult }: EvidencePageProps) {
  const evidence = latestResult?.evidence || [];
  const trust = latestResult?.trust;
  const security = latestResult?.security;

  if (!latestResult || evidence.length === 0) {
    return (
      <div className="bg-card rounded-lg border border-border shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <FileSearch size={20} className="text-primary" />
          <h2 className="text-base font-semibold text-foreground">Evidence Explorer</h2>
        </div>
        <p className="text-sm text-muted-foreground">
          Run a medication analysis from the Medical RAG workspace to see retrieved evidence sources,
          trust scores, and provenance chains here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-card rounded-lg border border-border shadow-sm p-5">
        <div className="flex items-center gap-2 mb-3">
          <FileSearch size={20} className="text-primary" />
          <h2 className="text-base font-semibold text-foreground">Evidence Explorer</h2>
          <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">
            {evidence.length} sources
          </span>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          {trust && (
            <div className="p-3 rounded-lg bg-primary-soft border border-primary/20">
              <div className="text-lg font-bold text-primary">{trust.overall_score.toFixed(2)}</div>
              <div className="text-xs text-primary">Trust Score ({trust.risk_class})</div>
            </div>
          )}
          <div className="p-3 rounded-lg bg-success-soft border border-success/30">
            <div className="text-lg font-bold text-success">{evidence.length}</div>
            <div className="text-xs text-success">Evidence Sources</div>
          </div>
          {security && (
            <div className={`p-3 rounded-lg border ${
              security.poisoning_status === 'ALLOW'
                ? 'bg-success-soft border-success/30'
                : 'bg-warning-soft border-warning/30'
            }`}>
              <div className="flex items-center justify-center gap-1">
                <Shield size={16} className={security.poisoning_status === 'ALLOW' ? 'text-success' : 'text-warning'} />
                <span className={`text-lg font-bold ${
                  security.poisoning_status === 'ALLOW' ? 'text-success' : 'text-warning'
                }`}>
                  {security.poisoning_status}
                </span>
              </div>
              <div className={`text-xs ${
                security.poisoning_status === 'ALLOW' ? 'text-success' : 'text-warning'
              }`}>Security Status</div>
            </div>
          )}
        </div>
      </div>

      {/* Evidence Items */}
      <div className="bg-card rounded-lg border border-border shadow-sm">
        <div className="p-4 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground">Retrieved Evidence</h3>
        </div>
        <div className="divide-y divide-border">
          {evidence.map((ev, i) => (
            <div key={ev.chunk_id || i} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-muted-foreground">[{i + 1}]</span>
                    <span className="text-sm font-medium text-foreground truncate">{ev.source_name || ev.title}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      ev.provenance_status === 'VERIFIED' ? 'bg-success-soft text-success' : 'bg-muted text-muted-foreground'
                    }`}>
                      {ev.provenance_status}
                    </span>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-3">{ev.text}</p>
                  <div className="flex flex-wrap gap-3 mt-2 text-[11px] text-muted-foreground">
                    {ev.pmid && <span>PMID: {ev.pmid}</span>}
                    {ev.doi && <span>DOI: {ev.doi}</span>}
                    <span>Authority: {(ev.source_authority ?? 0).toFixed(2)}</span>
                    <span>Trust: {(ev.trust_score ?? 0).toFixed(2)}</span>
                    <span>Freshness: {(ev.freshness ?? 0).toFixed(2)}</span>
                    <span>Method: {ev.retrieval_method}</span>
                  </div>
                </div>
                {ev.url && (
                  <a href={ev.url} target="_blank" rel="noopener noreferrer" className="p-1.5 text-muted-foreground hover:text-primary shrink-0">
                    <ExternalLink size={14} />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
