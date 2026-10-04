import { useState, useEffect } from 'react';
import { Activity, Check, X, Clock, AlertTriangle } from 'lucide-react';
import { fetchResearchState } from '../services/api';

const STATUS_CONFIG = {
  PASS: { icon: Check, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  BLOCKED: { icon: X, color: 'text-red-600', bg: 'bg-red-50' },
  PENDING: { icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50' },
  READY: { icon: Check, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  VALIDATED: { icon: Check, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  NOT_VALIDATED: { icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50' },
  NOT_CONFIGURED: { icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50' },
  CONFIGURED: { icon: Check, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  NOT_STARTED: { icon: AlertTriangle, color: 'text-slate-500', bg: 'bg-slate-50' },
} as const;

export function AuditPage() {
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
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={20} className="text-blue-600" />
        <h2 className="text-base font-semibold text-slate-900">Research Audit Status</h2>
      </div>
      <div className="space-y-2">
        {AUDIT_ITEMS.map(({ label, status }) => {
          const config = STATUS_CONFIG[status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.NOT_STARTED;
          const Icon = config.icon;
          return (
            <div key={label} className={`flex items-center justify-between p-3 rounded-lg ${config.bg}`}>
              <span className="text-sm text-slate-700">{label}</span>
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
