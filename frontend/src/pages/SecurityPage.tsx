import { Icons } from '../ui/icons';
import type { AnalysisResult } from '../types';
import { SecurityChecks } from '../components/results/SecurityChecks';

interface SecurityPageProps {
  latestResult?: AnalysisResult | null;
}

/**
 * Standalone security view. No longer a top-level tab: the same checks now
 * render inside the Analyze results ("Security Checks"). Kept for reuse.
 */
export function SecurityPage({ latestResult }: SecurityPageProps) {
  return (
    <div className="space-y-4">
      <div className="bg-card rounded-lg border border-border shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <Icons.security size={20} className="text-primary" aria-hidden="true" />
          <h2 className="text-base font-semibold text-foreground">Security Dashboard</h2>
          {!latestResult && (
            <span className="text-xs text-muted-foreground bg-muted px-2 py-0.5 rounded">Awaiting analysis</span>
          )}
        </div>

        {!latestResult && (
          <p className="text-sm text-muted-foreground mb-4">
            Run a medication analysis to see real-time security gate results here.
          </p>
        )}

        <SecurityChecks result={latestResult} />
      </div>
    </div>
  );
}
