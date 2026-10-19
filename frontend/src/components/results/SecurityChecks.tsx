import { Icons } from '../../ui/icons';
import { SecurityStatusPill } from '../ui/StatusPill';
import type { AnalysisResult } from '../../types';

/**
 * The three security gates as compact rows: icon, name, status pill, detail. Gate logic unchanged.
 * `ended` means the analysis has finished, so a gate with no result did not run.
 */
export function SecurityChecks({ result, ended = false }: { result: AnalysisResult | null | undefined; ended?: boolean }) {
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
      // Without a trust result the evidence was never scored, which is not a flag.
      status: result?.trust ? (result.trust.is_eligible ? 'ALLOW' : 'FLAG') : 'NO_DATA',
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
              <SecurityStatusPill status={status === 'NO_DATA' ? null : status} ended={ended} />
            </div>
            {detail && <p className="mt-0.5 text-xs text-muted-foreground">{detail}</p>}
            {!detail && ended && status === 'NO_DATA' && (
              <p className="mt-0.5 text-xs text-muted-foreground">The analysis stopped before this check ran.</p>
            )}
          </div>
        </li>
      ))}
    </ul>
  );
}
