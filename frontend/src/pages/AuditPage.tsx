import { Activity, Check, X, Clock, AlertTriangle } from 'lucide-react';

const AUDIT_ITEMS = [
  { label: 'Dataset Integrity', status: 'PASS' as const },
  { label: 'Case Order Integrity', status: 'PASS' as const },
  { label: 'Frozen Retrieval', status: 'PASS' as const },
  { label: 'Trust / Evidence Control', status: 'PASS' as const },
  { label: 'Claim Verification', status: 'PASS' as const },
  { label: 'Controlled Abstention', status: 'PASS' as const },
  { label: 'Prompt Freeze', status: 'BLOCKED' as const },
  { label: 'Researcher Authorization', status: 'PENDING' as const },
  { label: 'Real-LLM Evaluation', status: 'NOT_EXECUTED' as const },
];

const STATUS_CONFIG = {
  PASS: { icon: Check, color: 'text-emerald-600', bg: 'bg-emerald-50' },
  BLOCKED: { icon: X, color: 'text-red-600', bg: 'bg-red-50' },
  PENDING: { icon: Clock, color: 'text-amber-600', bg: 'bg-amber-50' },
  NOT_EXECUTED: { icon: AlertTriangle, color: 'text-slate-500', bg: 'bg-slate-50' },
} as const;

export function AuditPage() {
  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
      <div className="flex items-center gap-2 mb-4">
        <Activity size={20} className="text-blue-600" />
        <h2 className="text-base font-semibold text-slate-900">Research Audit Status</h2>
      </div>
      <div className="space-y-2">
        {AUDIT_ITEMS.map(({ label, status }) => {
          const config = STATUS_CONFIG[status];
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
