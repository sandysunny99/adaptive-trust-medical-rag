import { Icons } from '../../ui/icons';
import { SecurityStatusPill } from '../ui/StatusPill';
import type { AnalysisResult } from '../../types';

/** The three security gates as compact rows: icon, name, status pill, detail. Gate logic unchanged. */
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

  return (
    <ul className="divide-y divide-border">
      {gates.map(({ label, icon: GateIcon, status, detail }) => (
        <li key={label} className="flex flex-wrap items-start gap-x-3 gap-y-1 py-3 first:pt-0 last:pb-0">
          <GateIcon size={20} className="mt-0.5 shrink-0 text-muted-foreground" />
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h4 className="text-sm font-medium text-foreground">{label}</h4>
              <SecurityStatusPill status={status === 'NO_DATA' ? null : status} />
            </div>
            {detail && <p className="mt-0.5 text-xs text-muted-foreground">{detail}</p>}
          </div>
        </li>
      ))}
    </ul>
  );
}
