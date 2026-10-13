import { FileSearch } from 'lucide-react';
import type { AnalysisResult } from '../types';

export function EvidencePage({ result }: { result: AnalysisResult | null }) {
  if (!result) {
    return <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6"><h2 className="text-base font-semibold text-slate-900">Evidence Explorer</h2><p className="text-sm text-slate-500 mt-2">No analysis result is available yet.</p></div>;
  }
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <FileSearch size={20} className="text-blue-600" />
        <h2 className="text-base font-semibold text-slate-900">Evidence Explorer</h2>
      </div>
      <p className="text-sm text-slate-500">Request: {result.request_id} · Gate: {result.gate_decision}</p>
      </div>
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        {result.evidence.length === 0 ? <p className="text-sm text-slate-500">{result.abstention_reason || 'Evidence was not available for this analysis.'}</p> : result.evidence.map(item => (
          <article key={item.chunk_id} className="border-b border-slate-100 py-4 last:border-0">
            <div className="flex justify-between gap-3"><h3 className="text-sm font-semibold text-slate-900">{item.source_name || 'Unnamed source'}</h3><span className="text-xs text-slate-500">Trust: {item.trust_score.toFixed(2)}</span></div>
            <p className="text-xs text-slate-500 mt-1">{item.title} · {item.provenance_status}</p>
            <p className="text-sm text-slate-700 mt-2">{item.text}</p>
            <div className="flex gap-3 text-xs text-slate-500 mt-2">{item.pmid && <span>PMID: {item.pmid}</span>}{item.doi && <span>DOI: {item.doi}</span>}{item.url && <a href={item.url} target="_blank" rel="noreferrer" className="text-blue-600">Source</a>}</div>
          </article>
        ))}
      </div>
    </div>
  );
}
