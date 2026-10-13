import { Icons } from '../ui/icons';
import { useResearchState } from '../hooks/useResearchState';
import { ErrorState } from '../components/ui/ErrorState';

const STATUS_CONFIG = {
  PASS: { icon: Icons.pass, color: 'text-success', bg: 'bg-success-soft' },
  BLOCKED: { icon: Icons.block, color: 'text-destructive', bg: 'bg-destructive-soft' },
  PENDING: { icon: Icons.pending, color: 'text-warning', bg: 'bg-warning-soft' },
  READY: { icon: Icons.pass, color: 'text-success', bg: 'bg-success-soft' },
  VALIDATED: { icon: Icons.pass, color: 'text-success', bg: 'bg-success-soft' },
  NOT_VALIDATED: { icon: Icons.caution, color: 'text-warning', bg: 'bg-warning-soft' },
  NOT_CONFIGURED: { icon: Icons.caution, color: 'text-warning', bg: 'bg-warning-soft' },
  CONFIGURED: { icon: Icons.pass, color: 'text-success', bg: 'bg-success-soft' },
  NOT_STARTED: { icon: Icons.pending, color: 'text-muted-foreground', bg: 'bg-muted' },
} as const;

export function AuditPage() {
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

  const AUDIT_ITEMS = [
    { label: 'Dataset Integrity', status: state.dataset_integrity.status },
    { label: 'Case Order Integrity', status: state.case_order_integrity.status },
    { label: 'Frozen Retrieval', status: state.frozen_retrieval.status },
    { label: 'Trust / Evidence Control', status: state.trust_evidence_control.status },
    { label: 'Claim Verification', status: state.claim_verification.status },
    { label: 'Controlled Abstention', status: state.controlled_abstention.status },
    { label: 'Prompt Freeze', status: state.prompt_freeze.status },
    { label: 'Provider Readiness', status: state.provider_readiness.status },
    { label: 'Researcher Authorization', status: state.researcher_authorization.status },
    { label: 'Real-LLM Evaluation', status: state.real_llm_evaluation.status },
  ];

  return (
    <div className="bg-card rounded-lg border border-border shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Icons.audit size={20} className="text-primary" />
        <h2 className="text-base font-semibold text-foreground">Research Audit Status</h2>
      </div>
      <div className="space-y-2">
        {AUDIT_ITEMS.map(({ label, status }) => {
          const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.NOT_STARTED;
          const Icon = config.icon;
          return (
            <div key={label} className={`flex items-center justify-between p-3 rounded-lg ${config.bg}`}>
              <span className="text-sm text-foreground">{label}</span>
              <span className={`flex items-center gap-1.5 text-xs font-medium ${config.color}`}>
                <Icon size={14} />
                {status.replace(/_/g, ' ')}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
