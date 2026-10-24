import type { AnalysisResult, EvidenceItem } from '../types';
import { MedicationCard } from './MedicationCard';
import { Icons } from '../ui/icons';
import { disclaimerFor } from '../constants/disclaimer';
import { Disclosure } from './ui/Disclosure';
import { StatusPill } from './ui/StatusPill';
import { TrustSummary } from './results/TrustSummary';
import { EvidenceList, ExcludedSourceList } from './results/EvidenceList';
import { SecurityChecks } from './results/SecurityChecks';
import { citedSourceNumbers, verifiedHref } from '../services/evidenceDisplay';

interface ResultPanelProps {
  result: AnalysisResult;
  /** Show Evidence & Sources and Security Checks (only once an analysis has finished). */
  showDetails?: boolean;
}

// QUANTITY covers frequencies too ("daily", "per day"), as the backend's cue does.
const DETAIL_WORDS: Record<string, string> = {
  QUANTITY: 'an amount or frequency', TIMING: 'a timing', CERTAINTY: 'a certainty',
};

/** Plain wording for a claim-strength code; an unknown code gets a generic line, never backend text. */
function strengthReason(code: string, details: string[] = []): string {
  switch (code) {
    case 'ACTION_TOO_STRONG':
      return 'A statement was worded more strongly than the reviewed wording of its source supports.';
    case 'UNSUPPORTED_DETAIL': {
      const words = details.map(d => DETAIL_WORDS[d] ?? 'a detail');
      return `A statement added ${words.length ? words.join(' and ') : 'a detail'} that its source's reviewed wording does not state.`;
    }
    case 'NO_REVIEWED_RELATIONSHIP_WORDING':
      return 'No reviewed statement is available for this medication relationship, so no claim about it could be released.';
    case 'NO_REVIEWED_FOOD_WORDING':
      return 'No reviewed statement is available for this food or drink guidance, so it could not be released.';
    default:
      return "A statement could not be verified against its source's reviewed wording.";
  }
}

export function ResultPanel({ result, showDetails = true }: ResultPanelProps) {
  // Each distinct reason once; only for an abstention (a released answer has no withheld claims).
  const strengthReasons = result.gate_decision === 'abstain'
    ? [...new Set((result.claims || []).filter(c => c.strength_code)
        .map(c => strengthReason(c.strength_code as string, c.strength_details)))]
    : [];
  return (
    <div className="space-y-4">
      {/* Medications Identified */}
      <section className="bg-card rounded-lg border border-border shadow-sm">
        <div className="p-4 border-b border-border">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Icons.medication size={20} className="text-primary" />
            Medications Identified
          </h3>
        </div>
        <div className="p-4 grid gap-3">
          {(result.medications || []).map((med, i) => (
            <MedicationCard key={i} medication={med} />
          ))}
        </div>
      </section>

      {/* Drug-Drug Interactions */}
      {(result.interactions || []).length > 0 && (
        <section className="bg-card rounded-lg border border-border shadow-sm">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Icons.interactions size={20} className="text-primary" />
              Drug-Drug Interactions
            </h3>
          </div>
          <div className="p-4 space-y-3">
            {(result.interactions || []).map((interaction, i) => (
              <div key={i} className={`rounded-lg border p-3 ${
                interaction.interaction_detected
                  ? 'border-warning/30 bg-warning-soft'
                  : 'border-border bg-muted'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    {interaction.drug_a} ↔ {interaction.drug_b}
                  </span>
                  {interaction.interaction_detected
                    ? <StatusPill icon={Icons.caution} label="VERIFIED" tone="warning" />
                    : <StatusPill icon={Icons.pending} label="No verified evidence" tone="muted" />}
                </div>
                {interaction.potential_effect && (
                  <p className="text-xs text-muted-foreground mt-1">{interaction.potential_effect}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Food & Administration */}
      {(result.food_guidance || []).length > 0 ? (
        <section className="bg-card rounded-lg border border-border shadow-sm">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Icons.food size={20} className="text-primary" />
              Food &amp; Administration
            </h3>
          </div>
          <div className="p-4 space-y-2">
            {(result.food_guidance || []).map((fg, i) => (
              <div key={i} className="p-3 rounded border border-border">
                <div className="flex items-center justify-between gap-2">
                  <div>
                    <span className="text-sm font-medium text-foreground">{fg.drug}</span>
                    <p className="text-xs text-muted-foreground">{fg.administration}</p>
                  </div>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                    fg.evidence_status === 'VERIFIED' ? 'bg-success-soft text-success' :
                    fg.evidence_status === 'LIMITED' ? 'bg-warning-soft text-warning' :
                    'bg-muted text-muted-foreground'
                  }`}>
                    {fg.food_relationship.replace(/_/g, ' ')}
                  </span>
                </div>
                {fg.timing && <p className="mt-1 text-xs text-foreground">Timing: {fg.timing}</p>}
                {(fg.food_interactions || []).length > 0 && (
                  <ul className="mt-1 list-disc pl-5 text-xs text-foreground">
                    {fg.food_interactions.map((f, j) => <li key={j}>{f}</li>)}
                  </ul>
                )}
                <FoodCitations numbers={citedSourceNumbers(fg.source, ...(fg.food_interactions || []))}
                  evidence={result.evidence || []} />
              </div>
            ))}
          </div>
        </section>
      ) : showDetails && (
        <section aria-label="Food and dietary guidance" className="bg-card rounded-lg border border-border shadow-sm p-4">
          <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Icons.food size={20} className="text-primary" />
            Food &amp; Diet Guidance
          </h3>
          <p className="mt-1 text-sm text-muted-foreground">
            No food or dietary guidance could be verified from the available sources for this analysis.
            This does not mean there are no food or dietary issues; ask a pharmacist or clinician.
          </p>
        </section>
      )}

      {/* Conclusion */}
      <section aria-labelledby="conclusion-heading" className="bg-card rounded-lg border border-border shadow-sm">
        <div className="p-4 border-b border-border flex flex-wrap items-center justify-between gap-2">
          <h3 id="conclusion-heading" className="text-sm font-semibold text-foreground flex items-center gap-2">
            <Icons.conclusion size={20} className="text-primary" />
            Overall Conclusion
          </h3>
          {result.used_model && (
            <span className="text-xs bg-muted text-foreground px-2.5 py-1 rounded border border-border font-medium break-all">
              Model: <span className="font-semibold text-primary">{result.used_model.model_id}</span> ({result.used_model.provider})
            </span>
          )}
        </div>
        <div className="p-4">
          {result.gate_decision === 'abstain' ? (
            <div role="status" className="rounded-lg border border-border bg-muted p-3">
              <p className="text-sm font-semibold text-foreground">The system abstained from answering.</p>
              <p className="text-sm text-muted-foreground mt-1">
                {result.abstention_reason || 'The evidence was not strong enough to answer safely.'}
              </p>
              {strengthReasons.length > 0 && (
                <>
                  <p className="text-sm text-foreground mt-2">Why claims were withheld at their wording:</p>
                  <ul className="mt-1 list-disc pl-5 text-sm text-muted-foreground">
                    {strengthReasons.map(reason => <li key={reason}>{reason}</li>)}
                  </ul>
                  <p className="text-xs text-muted-foreground mt-2">
                    Withheld claims are not shown. Their absence does not mean the medicines are safe together.
                  </p>
                </>
              )}
            </div>
          ) : (
            <p className="text-sm text-foreground">{result.conclusion}</p>
          )}
          <div role="note" aria-label="Research disclaimer" className="mt-3 flex items-start gap-2 p-3 bg-warning-soft rounded-lg border border-warning/30">
            <Icons.caution size={14} className="mt-0.5 shrink-0 text-warning" aria-hidden="true" />
            <p className="text-xs font-medium text-foreground">{disclaimerFor(result.disclaimer)}</p>
          </div>
        </div>
      </section>

      <TrustSummary trust={result.trust} />

      {showDetails && (
        <>
          <Disclosure
            defaultOpen
            className="bg-card shadow-sm"
            icon={<Icons.evidence size={20} />}
            title={`Evidence & Sources (${(result.evidence || []).length})`}
          >
            {(result.evidence || []).length > 0
              ? <EvidenceList evidence={result.evidence} />
              : <p className="text-sm text-muted-foreground">
                  {result.gate_decision === 'abstain'
                    ? 'No evidence passed the eligibility checks for this analysis.'
                    : 'No evidence items were returned for this analysis.'}
                </p>}
          </Disclosure>

          {(result.excluded_sources || []).length > 0 && (
            <Disclosure
              className="bg-card shadow-sm"
              icon={<Icons.caution size={20} />}
              title={`Excluded sources (${result.excluded_sources!.length})`}
            >
              <ExcludedSourceList sources={result.excluded_sources!} />
            </Disclosure>
          )}

          <Disclosure
            defaultOpen
            className="bg-card shadow-sm"
            icon={<Icons.security size={20} />}
            title="Security Checks"
          >
            <SecurityChecks result={result} ended />
          </Disclosure>
        </>
      )}
    </div>
  );
}

/** Each cited source of a food statement: a link to the exact verified document, or why it is not one. */
function FoodCitations({ numbers, evidence }: { numbers: number[]; evidence: EvidenceItem[] }) {
  if (numbers.length === 0) return null;
  return (
    <p className="mt-1 flex flex-wrap gap-x-3 text-[11px] text-muted-foreground">
      {numbers.map(n => {
        const ev = evidence[n - 1];
        const href = ev && verifiedHref(ev);
        const label = ev?.source_title || ev?.document_id || `Source ${n}`;
        return href ? (
          <a key={n} href={href} target="_blank" rel="noopener noreferrer"
            className="rounded text-primary hover:underline focus:outline-none focus-visible:ring-2 focus-visible:ring-ring">
            Source {n}: {label} (opens in new tab)
          </a>
        ) : (
          <span key={n}>Source {n}: {ev ? 'not a verified link' : 'not among the returned evidence'}</span>
        );
      })}
    </p>
  );
}
