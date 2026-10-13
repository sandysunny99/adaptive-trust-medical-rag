import { FileSearch, Shield } from 'lucide-react';
import type { AnalysisResult } from '../types';
import { EvidenceList } from '../components/results/EvidenceList';

interface EvidencePageProps {
  latestResult?: AnalysisResult | null;
}

/**
 * Standalone evidence view. No longer a top-level tab: the same list now renders
 * inside the Analyze results ("Evidence & Sources"). Kept for reuse.
 */
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
          Run a medication analysis to see retrieved evidence sources,
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
        <div className="p-4">
          <EvidenceList evidence={evidence} />
        </div>
      </div>
    </div>
  );
}
