import { Shield } from 'lucide-react';
import type { AnalysisResult } from '../types';

export function SecurityPage({ result }: { result: AnalysisResult | null }) {
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={20} className="text-blue-600" />
          <h2 className="text-base font-semibold text-slate-900">Security Dashboard</h2>
        </div>
        {!result?.security ? <p className="text-sm text-slate-500">No analysis security events are available yet.</p> : (
          <div className="grid grid-cols-2 gap-4">
            <div className="p-4 rounded border"><h3 className="text-sm font-medium">Prompt injection</h3><p className="text-sm mt-1">{result.security.injection_status}</p></div>
            <div className="p-4 rounded border"><h3 className="text-sm font-medium">Retrieval poisoning</h3><p className="text-sm mt-1">{result.security.poisoning_status}</p><p className="text-xs text-slate-500 mt-1">{result.security.poisoning_reason || 'No blocking reason reported.'}</p></div>
            <div className="col-span-2 text-xs text-slate-500">Request: {result.request_id} · Gate: {result.gate_decision}</div>
          </div>
        )}
      </div>
    </div>
  );
}
