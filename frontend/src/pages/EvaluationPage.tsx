import { useState, useEffect } from 'react';
import { BarChart3, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { fetchResearchState } from '../services/api';

export function EvaluationPage() {
  const [state, setState] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchResearchState()
      .then(res => {
        setState(res);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch research state:", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return <div className="p-6">Loading research state...</div>;
  }

  if (!state) {
    return <div className="p-6 text-red-500">Failed to load research state.</div>;
  }

  const isBlocked = state.prompt_freeze === 'BLOCKED' || state.provider_readiness === 'BLOCKED' || state.dataset_integrity === 'BLOCKED';

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 size={20} className="text-blue-600" />
          <h2 className="text-base font-semibold text-slate-900">Research Evaluation</h2>
        </div>

        <div className={`p-4 border rounded-lg ${isBlocked ? 'bg-amber-50 border-amber-200' : 'bg-blue-50 border-blue-200'}`}>
          <div className="flex items-center gap-2">
            {isBlocked ? <AlertTriangle size={16} className="text-amber-600" /> : <CheckCircle2 size={16} className="text-blue-600" />}
            <span className={`text-sm font-medium ${isBlocked ? 'text-amber-800' : 'text-blue-800'}`}>
              REAL-LLM {state.protocol.replace('REAL_LLM_EVALUATION_PROTOCOL_', '')} EVALUATION
            </span>
          </div>
          <div className={`mt-2 text-xs space-y-1 ${isBlocked ? 'text-amber-700' : 'text-blue-700'}`}>
            <p><strong>Status:</strong> {isBlocked ? 'BLOCKED / NOT STARTED' : 'READY / NOT STARTED'}</p>
            <p><strong>Protocol:</strong> {state.protocol}</p>
            <p><strong>Prompt Freeze:</strong> {state.prompt_freeze}</p>
            <p><strong>Provider Readiness:</strong> {state.provider_readiness}</p>
            <p><strong>Researcher Authorization:</strong> {state.researcher_authorization}</p>
            <p><strong>Medical Evaluation Requests:</strong> {state.medical_evaluation_requests_executed} / {state.medical_evaluation_requests_total}</p>
          </div>
        </div>

        <div className="mt-4 grid grid-cols-5 gap-3">
          {[
            { label: 'Claim Support Rate', value: '—' },
            { label: 'Citation Validation', value: '—' },
            { label: 'Unsupported Answer', value: '—' },
            { label: 'Abstention Rate', value: '—' },
            { label: 'Provider Failure', value: '—' },
          ].map(({ label, value }) => (
            <div key={label} className="p-3 rounded border border-slate-200 text-center">
              <div className="text-lg font-bold text-slate-400">{value}</div>
              <div className="text-xs text-slate-500 mt-1">{label}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-slate-400 mt-3">
          Metrics will be populated exclusively from frozen result artifacts after authorized execution.
        </p>
      </div>
    </div>
  );
}
