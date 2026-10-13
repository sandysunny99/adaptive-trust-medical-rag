import { Icons } from '../../ui/icons';
import { SecurityStatusPill } from '../ui/StatusPill';
import type { AnalysisResult } from '../../types';

/** The three security gate cards, moved from the former Security tab unchanged in logic. */
export function SecurityChecks({ result }: { result: AnalysisResult | null | undefined }) {
  const security = result?.security;

  const gates = [
    {
      label: 'Prompt Injection',
      icon: Icons.promptInjection,
      status: security?.injection_status || 'NO_DATA',
      detail: security ? (
        (security.injection_markers || []).length > 0
          ? `Detected: ${security.injection_markers.join(', ')}`
          : 'No injection markers detected'
      ) : null,
    },
    {
      label: 'Retrieval Poisoning',
      icon: Icons.retrievalPoisoning,
      status: security?.poisoning_status || 'NO_DATA',
      detail: security?.poisoning_reason || (security ? 'No poisoned chunks detected' : null),
    },
    {
      label: 'Evidence Integrity',
      icon: Icons.evidenceIntegrity,
      status: result?.trust?.is_eligible ? 'ALLOW' : (result ? 'FLAG' : 'NO_DATA'),
      detail: result?.trust
        ? `Trust: ${result.trust.overall_score.toFixed(2)} / threshold ${result.trust.threshold.toFixed(2)} (${result.trust.risk_class})`
        : null,
    },
  ];

  const surface: Record<string, string> = {
    ALLOW: 'border-success/30 bg-success-soft',
    FLAG: 'border-warning/30 bg-warning-soft',
    BLOCK: 'border-destructive/30 bg-destructive-soft',
  };

  return (
    <ul className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {gates.map(({ label, icon: GateIcon, status, detail }) => (
        <li key={label} className={`p-4 rounded-lg border ${surface[status] ?? 'border-border bg-muted'}`}>
          <h4 className="flex items-center gap-2 text-sm font-medium text-foreground">
            <GateIcon size={20} className="text-muted-foreground" />
            {label}
          </h4>
          <div className="mt-2">
            <SecurityStatusPill status={status === 'NO_DATA' ? null : status} />
          </div>
          {detail && (
            <p className="text-xs text-foreground mt-2">{detail}</p>
          )}
        </li>
      ))}
    </ul>
  );
}
