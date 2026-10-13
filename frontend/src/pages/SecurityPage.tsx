import { Shield, ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';
import type { AnalysisResult } from '../types';

interface SecurityPageProps {
  latestResult?: AnalysisResult | null;
}

export function SecurityPage({ latestResult }: SecurityPageProps) {
  const security = latestResult?.security;

  const gates = [
    {
      label: 'Prompt Injection',
      status: security?.injection_status || 'NO_DATA',
      detail: security ? (
        (security.injection_markers || []).length > 0
          ? `Detected: ${security.injection_markers.join(', ')}`
          : 'No injection markers detected'
      ) : null,
    },
    {
      label: 'Retrieval Poisoning',
      status: security?.poisoning_status || 'NO_DATA',
      detail: security?.poisoning_reason || (security ? 'No poisoned chunks detected' : null),
    },
    {
      label: 'Evidence Integrity',
      status: latestResult?.trust?.is_eligible ? 'ALLOW' : (latestResult ? 'FLAG' : 'NO_DATA'),
      detail: latestResult?.trust
        ? `Trust: ${latestResult.trust.overall_score.toFixed(2)} / threshold ${latestResult.trust.threshold.toFixed(2)} (${latestResult.trust.risk_class})`
        : null,
    },
  ];

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'ALLOW':
        return { Icon: ShieldCheck, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-800' };
      case 'FLAG':
        return { Icon: ShieldAlert, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', badge: 'bg-amber-100 text-amber-800' };
      case 'BLOCK':
        return { Icon: AlertTriangle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-800' };
      default:
        return { Icon: Shield, color: 'text-slate-400', bg: 'bg-slate-50', border: 'border-slate-200', badge: 'bg-slate-100 text-slate-600' };
    }
  };

  return (
    <div className="space-y-4">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Shield size={20} className="text-blue-600" />
          <h2 className="text-base font-semibold text-slate-900">Security Dashboard</h2>
          {!latestResult && (
            <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded">Awaiting analysis</span>
          )}
        </div>

        {!latestResult && (
          <p className="text-sm text-slate-500 mb-4">
            Run a medication analysis from the Medical RAG workspace to see real-time security gate results here.
          </p>
        )}

        <div className="grid grid-cols-3 gap-4">
          {gates.map(({ label, status, detail }) => {
            const cfg = getStatusConfig(status);
            return (
              <div key={label} className={`p-4 rounded-lg border ${cfg.border} ${cfg.bg}`}>
                <cfg.Icon size={18} className={cfg.color} />
                <h3 className="text-sm font-medium text-slate-900 mt-2">{label}</h3>
                <span className={`text-xs font-medium px-2 py-0.5 rounded-full inline-block mt-1 ${cfg.badge}`}>
                  {status === 'NO_DATA' ? 'PENDING' : status}
                </span>
                {detail && (
                  <p className="text-[11px] text-slate-500 mt-2">{detail}</p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
