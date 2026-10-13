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
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <FileSearch size={20} className="text-blue-600" />
          <h2 className="text-base font-semibold text-slate-900">Evidence Explorer</h2>
        </div>
        <p className="text-sm text-slate-500">
          Run a medication analysis from the Medical RAG workspace to see retrieved evidence sources,
          trust scores, and provenance chains here.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
        <div className="flex items-center gap-2 mb-3">
          <FileSearch size={20} className="text-blue-600" />
          <h2 className="text-base font-semibold text-slate-900">Evidence Explorer</h2>
          <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
            {evidence.length} sources
          </span>
        </div>
        <div className="grid grid-cols-3 gap-4 text-center">
          {trust && (
            <div className="p-3 rounded-lg bg-blue-50 border border-blue-100">
              <div className="text-lg font-bold text-blue-700">{trust.overall_score.toFixed(2)}</div>
              <div className="text-xs text-blue-600">Trust Score ({trust.risk_class})</div>
            </div>
          )}
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-100">
            <div className="text-lg font-bold text-emerald-700">{evidence.length}</div>
            <div className="text-xs text-emerald-600">Evidence Sources</div>
          </div>
          {security && (
            <div className={`p-3 rounded-lg border ${
              security.poisoning_status === 'ALLOW'
                ? 'bg-emerald-50 border-emerald-100'
                : 'bg-amber-50 border-amber-100'
            }`}>
              <div className="flex items-center justify-center gap-1">
                <Shield size={16} className={security.poisoning_status === 'ALLOW' ? 'text-emerald-600' : 'text-amber-600'} />
                <span className={`text-lg font-bold ${
                  security.poisoning_status === 'ALLOW' ? 'text-emerald-700' : 'text-amber-700'
                }`}>
                  {security.poisoning_status}
                </span>
              </div>
              <div className={`text-xs ${
                security.poisoning_status === 'ALLOW' ? 'text-emerald-600' : 'text-amber-600'
              }`}>Security Status</div>
            </div>
          )}
        </div>
      </div>

      {/* Evidence Items */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm">
        <div className="p-4 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-900">Retrieved Evidence</h3>
        </div>
        <div className="divide-y divide-slate-100">
          {evidence.map((ev, i) => (
            <div key={ev.chunk_id || i} className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-400">[{i + 1}]</span>
                    <span className="text-sm font-medium text-slate-900 truncate">{ev.source_name || ev.title}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                      ev.provenance_status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {ev.provenance_status}
                    </span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1 line-clamp-3">{ev.text}</p>
                  <div className="flex flex-wrap gap-3 mt-2 text-[11px] text-slate-400">
                    {ev.pmid && <span>PMID: {ev.pmid}</span>}
                    {ev.doi && <span>DOI: {ev.doi}</span>}
                    <span>Authority: {(ev.source_authority ?? 0).toFixed(2)}</span>
                    <span>Trust: {(ev.trust_score ?? 0).toFixed(2)}</span>
                    <span>Freshness: {(ev.freshness ?? 0).toFixed(2)}</span>
                    <span>Method: {ev.retrieval_method}</span>
                  </div>
                </div>
                {ev.url && (
                  <a href={ev.url} target="_blank" rel="noopener noreferrer" className="p-1.5 text-slate-400 hover:text-blue-600 shrink-0">
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
