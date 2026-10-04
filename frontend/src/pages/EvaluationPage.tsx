import { BarChart3, AlertTriangle } from 'lucide-react';

export function EvaluationPage() {
  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 size={20} className="text-blue-600" />
          <h2 className="text-base font-semibold text-slate-900">Research Evaluation</h2>
        </div>

        <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center gap-2">
            <AlertTriangle size={16} className="text-amber-600" />
            <span className="text-sm font-medium text-amber-800">Real-LLM V1.1 Evaluation</span>
          </div>
          <div className="mt-2 text-xs text-amber-700 space-y-1">
            <p><strong>Status:</strong> BLOCKED / NOT EXECUTED</p>
            <p><strong>Prompt Freeze:</strong> BLOCKED (source missing)</p>
            <p><strong>Researcher Authorization:</strong> PENDING</p>
            <p><strong>Medical Evaluation Requests:</strong> 0 / 160</p>
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
