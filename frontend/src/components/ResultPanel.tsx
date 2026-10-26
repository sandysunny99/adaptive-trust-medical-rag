import type { AnalysisResult, ClaimInfo, EvidenceItem, FoodGuidanceStatus } from '../types';
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

export function ResultPanel({ result, showDetails = true }: ResultPanelProps) {
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
            {foodStatusText(result.food_guidance_status)}
            {' '}This does not mean there are no food or dietary issues; ask a pharmacist or clinician.
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

          {(result.claims || []).length > 0 && (
            <Disclosure
              defaultOpen={result.gate_decision === 'abstain'}
              className="bg-card shadow-sm"
              icon={<Icons.conclusion size={20} />}
              title={`Claim verification (${verifiedCount(result.claims)} of ${result.claims.length} verified)`}
            >
              <ClaimList claims={result.claims} />
            </Disclosure>
          )}

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


const FOOD_STATUS_TEXT: Record<FoodGuidanceStatus, string> = {
  VERIFIED: 'Verified food guidance is shown above.',
  NONE_FOUND: 'The verified evidence for this analysis contains no food or dietary guidance.',
  NOT_VERIFIED: 'Food or dietary guidance was generated, but it could not be verified against the sources, so it is not shown.',
  WITHHELD: 'The answer was withheld, so no food or dietary guidance is shown, even though its own statements were verified.',
  NOT_RUN: 'Food and dietary guidance was not assessed, because the analysis stopped before an answer was generated.',
};

/** What happened to food guidance; without a status, the older generic wording. */
function foodStatusText(status: FoodGuidanceStatus | undefined): string {
  return (status && FOOD_STATUS_TEXT[status])
    || 'No food or dietary guidance could be verified from the available sources for this analysis.';
}

function verifiedCount(claims: ClaimInfo[]): number {
  return claims.filter(c => c.support_state === 'SUPPORTED').length;
}

const FIELD_LABELS: Record<string, string> = {
  conclusion: 'Conclusion', interactions: 'Interaction', adverse_reactions: 'Adverse reaction',
  warnings: 'Warning', food_guidance: 'Food guidance', patient_considerations: 'Patient consideration',
  claims_for_verification: 'Claim',
};

/** Every generated statement with its verification result, so a withheld answer shows which failed. */
export function ClaimList({ claims }: { claims: ClaimInfo[] }) {
  return (
    <ul className="space-y-2">
      {claims.map(c => {
        const ok = c.support_state === 'SUPPORTED';
        const why = c.invalid_source_references?.length ? `Cites a source that was not retrieved: ${c.invalid_source_references.join(', ')}`
          : !c.citation_present ? 'Cites no source'
          : c.strength_check ? `Stronger than its source: ${c.strength_check}`
          : c.canonical_identity_reason && c.canonical_identity_status !== 'MATCH' ? c.canonical_identity_reason
          : null;
        return (
          <li key={c.claim_id} className="rounded border border-border p-2">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <span className="text-[11px] font-medium text-muted-foreground">{FIELD_LABELS[c.field ?? ''] ?? c.field ?? 'Statement'}</span>
              <StatusPill icon={ok ? Icons.pass : Icons.caution} label={ok ? 'Verified' : c.support_state.replace(/_/g, ' ')}
                tone={ok ? 'success' : 'warning'} />
            </div>
            <p className="mt-1 text-xs text-foreground">{c.text}</p>
            {!ok && why && <p className="mt-1 text-[11px] text-muted-foreground">{why}</p>}
          </li>
        );
      })}
    </ul>
  );
}
