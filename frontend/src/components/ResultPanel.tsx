import type { AnalysisResult } from '../types';
import { MedicationCard } from './MedicationCard';
import { AlertTriangle, Utensils, FileText } from 'lucide-react';

interface ResultPanelProps {
  result: AnalysisResult;
}

export function ResultPanel({ result }: ResultPanelProps) {
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
      <section className="bg-card rounded-lg border border-border shadow-sm">
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="text-sm font-semibold text-foreground">Overall Conclusion</h3>
          {result.used_model && (
            <span className="text-xs bg-muted text-foreground px-2.5 py-1 rounded border border-border font-medium">
              Model: <span className="font-semibold text-primary">{result.used_model.model_id}</span> ({result.used_model.provider})
            </span>
          )}
        </div>
        <div className="p-4">
          <p className="text-sm text-foreground">{result.conclusion}</p>
          <div className="mt-3 p-3 bg-primary-soft rounded-lg border border-primary/20">
            <p className="text-xs text-primary">{result.disclaimer}</p>
          </div>
        </div>
      </section>

      {/* Verified Evidence */}
      {(result.evidence || []).length > 0 && (
        <section className="bg-card rounded-lg border border-border shadow-sm">
          <div className="p-4 border-b border-border">
            <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
              <FileText size={16} className="text-primary" />
              Verified Evidence ({(result.evidence || []).length})
            </h3>
          </div>
          <div className="p-4 space-y-2">
            {(result.evidence || []).map((ev, i) => (
              <div key={i} className="p-3 rounded border border-border text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-foreground">[{i + 1}] {ev.source_name}</span>
                  <span className="text-muted-foreground">{ev.retrieval_method}</span>
                </div>
                <p className="text-muted-foreground mt-1 line-clamp-2">{ev.text}</p>
                <div className="flex gap-3 mt-1 text-muted-foreground">
                  {ev.pmid && <span>PMID: {ev.pmid}</span>}
                  <span>Authority: {ev.source_authority.toFixed(2)}</span>
                  <span>Trust: {ev.trust_score.toFixed(2)}</span>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
