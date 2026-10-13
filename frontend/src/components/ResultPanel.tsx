import type { AnalysisResult } from '../types';
import { MedicationCard } from './MedicationCard';
import { AlertTriangle, Utensils, FileText, Shield } from 'lucide-react';
import { disclaimerFor } from '../constants/disclaimer';
import { Disclosure } from './ui/Disclosure';
import { TrustSummary } from './results/TrustSummary';
import { EvidenceList } from './results/EvidenceList';
import { SecurityChecks } from './results/SecurityChecks';

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
          <h3 className="text-sm font-semibold text-foreground">Medications Identified</h3>
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
              <AlertTriangle size={16} className="text-warning" />
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
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                    interaction.interaction_detected
                      ? 'bg-warning-soft text-warning'
                      : 'bg-muted text-muted-foreground'
                  }`}>
                    {interaction.interaction_detected ? '⚠ VERIFIED' : 'No verified evidence'}
                  </span>
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
      {(result.food_guidance || []).length > 0 && (
        <section className="bg-card rounded-lg border border-border shadow-sm">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <Utensils size={16} className="text-success" />
              Food &amp; Administration
            </h3>
          </div>
          <div className="p-4 space-y-2">
            {(result.food_guidance || []).map((fg, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded border border-border">
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
            ))}
          </div>
        </section>
      )}

      {/* Conclusion */}
      <section aria-labelledby="conclusion-heading" className="bg-card rounded-lg border border-border shadow-sm">
        <div className="p-4 border-b border-border flex flex-wrap items-center justify-between gap-2">
          <h3 id="conclusion-heading" className="text-sm font-semibold text-foreground">Overall Conclusion</h3>
          {result.used_model && (
            <span className="text-xs bg-muted text-foreground px-2.5 py-1 rounded border border-border font-medium break-all">
              Model: <span className="font-semibold text-primary">{result.used_model.model_id}</span> ({result.used_model.provider})
            </span>
          )}
        </div>
        <div className="p-4">
          <p className="text-sm text-foreground">{result.conclusion}</p>
          <div role="note" aria-label="Research disclaimer" className="mt-3 flex items-start gap-2 p-3 bg-warning-soft rounded-lg border border-warning/30">
            <AlertTriangle size={14} className="mt-0.5 shrink-0 text-warning" aria-hidden="true" />
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
            icon={<FileText size={16} />}
            title={`Evidence & Sources (${(result.evidence || []).length})`}
          >
            {(result.evidence || []).length > 0
              ? <EvidenceList evidence={result.evidence} />
              : <p className="text-sm text-muted-foreground">No evidence items were returned for this analysis.</p>}
          </Disclosure>

          <Disclosure
            defaultOpen
            className="bg-card shadow-sm"
            icon={<Shield size={16} />}
            title="Security Checks"
          >
            <SecurityChecks result={result} />
          </Disclosure>
        </>
      )}
    </div>
  );
}
