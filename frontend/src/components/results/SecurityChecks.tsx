import { Shield, ShieldCheck, ShieldAlert, AlertTriangle } from 'lucide-react';
import type { AnalysisResult } from '../../types';

/** The three security gate cards, moved from the former Security tab unchanged in logic. */
export function SecurityChecks({ result }: { result: AnalysisResult | null | undefined }) {
  const security = result?.security;

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
      status: result?.trust?.is_eligible ? 'ALLOW' : (result ? 'FLAG' : 'NO_DATA'),
      detail: result?.trust
        ? `Trust: ${result.trust.overall_score.toFixed(2)} / threshold ${result.trust.threshold.toFixed(2)} (${result.trust.risk_class})`
        : null,
    },
  ];

  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'ALLOW':
        return { Icon: ShieldCheck, color: 'text-success', bg: 'bg-success-soft', border: 'border-success/30', badge: 'bg-card text-success' };
      case 'FLAG':
        return { Icon: ShieldAlert, color: 'text-warning', bg: 'bg-warning-soft', border: 'border-warning/30', badge: 'bg-card text-warning' };
      case 'BLOCK':
        return { Icon: AlertTriangle, color: 'text-destructive', bg: 'bg-destructive-soft', border: 'border-destructive/30', badge: 'bg-card text-destructive' };
      default:
        return { Icon: Shield, color: 'text-muted-foreground', bg: 'bg-muted', border: 'border-border', badge: 'bg-card text-muted-foreground' };
    }
  };

  return (
    <ul className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {gates.map(({ label, status, detail }) => {
        const cfg = getStatusConfig(status);
        return (
          <li key={label} className={`p-4 rounded-lg border ${cfg.border} ${cfg.bg}`}>
            <cfg.Icon size={18} className={cfg.color} aria-hidden="true" />
            <h4 className="text-sm font-medium text-foreground mt-2">{label}</h4>
            <span className={`text-xs font-semibold px-2 py-0.5 rounded-full inline-block mt-1 ${cfg.badge}`}>
              {status === 'NO_DATA' ? 'PENDING' : status}
            </span>
            {detail && (
              <p className="text-xs text-foreground mt-2">{detail}</p>
            )}
          </li>
        );
      })}
    </ul>
  );
}
