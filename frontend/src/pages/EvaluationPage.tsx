import { BarChart3, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { useResearchState } from '../hooks/useResearchState';
import { ErrorState } from '../components/ui/ErrorState';

export function EvaluationPage() {
  const { state, error, loading, reload } = useResearchState();

  if (loading && !state && !error) {
    return <div className="p-6 text-sm text-muted-foreground" role="status">Loading research state…</div>;
  }

  if (!state) {
    return (
      <ErrorState
        title="Couldn't load research state"
        message={error}
        onRetry={reload}
        retrying={loading}
      />
    );
  }

  const isBlocked = state.prompt_freeze.status === 'BLOCKED' || state.provider_readiness.status === 'BLOCKED' || state.dataset_integrity.status === 'BLOCKED';

  return (
    <div className="space-y-4">
      <div className="bg-card rounded-lg border border-border shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 size={20} className="text-primary" />
          <h2 className="text-base font-semibold text-foreground">Research Evaluation</h2>
        </div>

        <div className={`p-4 border rounded-lg ${isBlocked ? 'bg-warning-soft border-warning/30' : 'bg-primary-soft border-primary/30'}`}>
          <div className="flex items-center gap-2">
            {isBlocked ? <AlertTriangle size={16} className="text-warning" /> : <CheckCircle2 size={16} className="text-primary" />}
            <span className={`text-sm font-medium ${isBlocked ? 'text-warning' : 'text-primary'}`}>
              REAL-LLM {state.protocol.replace('REAL_LLM_EVALUATION_PROTOCOL_', '')} EVALUATION
            </span>
          </div>
          <div className={`mt-2 text-xs space-y-1 ${isBlocked ? 'text-warning' : 'text-primary'}`}>
            <p><strong>Status:</strong> {isBlocked ? 'BLOCKED / NOT STARTED' : 'READY / NOT STARTED'}</p>
            <p><strong>Protocol:</strong> {state.protocol}</p>
            <p><strong>Prompt Freeze:</strong> {state.prompt_freeze.status}</p>
            <p><strong>Provider Readiness:</strong> {state.provider_readiness.status}</p>
            <p><strong>Researcher Authorization:</strong> {state.researcher_authorization.status}</p>
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
            <div key={label} className="p-3 rounded border border-border text-center">
              <div className="text-lg font-bold text-muted-foreground">{value}</div>
              <div className="text-xs text-muted-foreground mt-1">{label}</div>
            </div>
          ))}
        </div>
        <p className="text-xs text-muted-foreground mt-3">
          Metrics will be populated exclusively from frozen result artifacts after authorized execution.
        </p>
      </div>
    </div>
  );
}
