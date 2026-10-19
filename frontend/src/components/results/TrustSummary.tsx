import { Icons } from '../../ui/icons';
import { RiskTierPill } from '../ui/StatusPill';
import type { TrustInfo } from '../../types';

export const NOT_AVAILABLE = 'Not available';

/**
 * Shows the backend's trust fields as returned. No frontend calculation:
 *   result.trust.overall_score, result.trust.threshold, result.trust.risk_class
 * Any missing field reads "Not available".
 */
function formatScore(value: unknown): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(2) : NOT_AVAILABLE;
}

function formatText(value: unknown): string {
  return typeof value === 'string' && value.trim() ? value : NOT_AVAILABLE;
}

export function TrustSummary({ trust }: { trust: TrustInfo | null | undefined }) {
  const rows = [
    { label: 'Trust score', value: formatScore(trust?.overall_score) },
    { label: 'Threshold', value: formatScore(trust?.threshold) },
    { label: 'Risk tier', value: formatText(trust?.risk_class) },
  ];

  return (
    <section aria-labelledby="trust-heading" className="bg-card rounded-lg border border-border shadow-sm">
      <div className="p-4 border-b border-border">
        <h3 id="trust-heading" className="text-sm font-semibold text-foreground flex items-center gap-2">
          <Icons.trust size={20} className="text-primary" />
          Evidence Trust
        </h3>
      </div>
      <dl className="grid grid-cols-1 sm:grid-cols-3 divide-y sm:divide-y-0 sm:divide-x divide-border">
        {rows.map(({ label, value }) => (
          <div key={label} className="p-4">
            <dt className="text-xs text-muted-foreground">{label}</dt>
            <dd
              className={
                value === NOT_AVAILABLE
                  ? 'mt-1 text-sm text-muted-foreground'
                  : 'mt-1 text-lg font-semibold text-foreground font-mono'
              }
            >
              {label === 'Risk tier' && value !== NOT_AVAILABLE ? <RiskTierPill tier={value} /> : value}
            </dd>
          </div>
        ))}
      </dl>
      {(trust?.risk_basis || (trust?.unrelated_excluded ?? 0) > 0) && (
        <div className="px-4 pb-4 space-y-1 text-xs text-muted-foreground">
          {trust?.risk_basis && <p>Risk tier basis: {trust.risk_basis}</p>}
          {(trust?.unrelated_excluded ?? 0) > 0 && (
            <p>{trust!.unrelated_excluded} retrieved chunk(s) named none of these medications and were excluded.</p>
          )}
        </div>
      )}
    </section>
  );
}
