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
      <section className="bg-white rounded-lg border border-slate-200 shadow-sm">
        <div className="p-4 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-900">Medications Identified</h3>
        </div>
        <div className="p-4 grid gap-3">
          {result.medications.map((med, i) => (
            <MedicationCard key={i} medication={med} />
          ))}
        </div>
      </section>

      {/* Drug-Drug Interactions */}
      {result.interactions.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 shadow-sm">
          <div className="p-4 border-b border-slate-100">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <AlertTriangle size={16} className="text-amber-600" />
              Drug-Drug Interactions
            </h3>
          </div>
          <div className="p-4 space-y-3">
            {result.interactions.map((interaction, i) => (
              <div key={i} className={`rounded-lg border p-3 ${
                interaction.interaction_detected
                  ? 'border-amber-200 bg-amber-50'
                  : 'border-slate-200 bg-slate-50'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">
                    {interaction.drug_a} ↔ {interaction.drug_b}
                  </span>
                  <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                    interaction.interaction_detected
                      ? 'bg-amber-100 text-amber-800'
                      : 'bg-slate-100 text-slate-600'
                  }`}>
                    {interaction.interaction_detected ? '⚠ VERIFIED' : 'No verified evidence'}
                  </span>
                </div>
                {interaction.potential_effect && (
                  <p className="text-xs text-slate-600 mt-1">{interaction.potential_effect}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Food & Administration */}
      {result.food_guidance.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 shadow-sm">
          <div className="p-4 border-b border-slate-100">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <Utensils size={16} className="text-green-600" />
              Food &amp; Administration
            </h3>
          </div>
          <div className="p-4 space-y-2">
            {result.food_guidance.map((fg, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded border border-slate-200">
                <div>
                  <span className="text-sm font-medium text-slate-900">{fg.drug}</span>
                  <p className="text-xs text-slate-600">{fg.administration}</p>
                </div>
                <span className={`text-xs font-medium px-2 py-0.5 rounded ${
                  fg.evidence_status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800' :
                  fg.evidence_status === 'LIMITED' ? 'bg-amber-100 text-amber-800' :
                  'bg-slate-100 text-slate-600'
                }`}>
                  {fg.food_relationship.replace(/_/g, ' ')}
                </span>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Conclusion */}
      <section className="bg-white rounded-lg border border-slate-200 shadow-sm">
        <div className="p-4 border-b border-slate-100">
          <h3 className="text-sm font-semibold text-slate-900">Overall Conclusion</h3>
        </div>
        <div className="p-4">
          <p className="text-sm text-slate-700">{result.conclusion}</p>
          <div className="mt-3 p-3 bg-blue-50 rounded-lg border border-blue-100">
            <p className="text-xs text-blue-800">{result.disclaimer}</p>
          </div>
        </div>
      </section>

      {/* Verified Evidence */}
      {result.evidence.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 shadow-sm">
          <div className="p-4 border-b border-slate-100">
            <h3 className="text-sm font-semibold text-slate-900 flex items-center gap-2">
              <FileText size={16} className="text-blue-600" />
              Verified Evidence ({result.evidence.length})
            </h3>
          </div>
          <div className="p-4 space-y-2">
            {result.evidence.map((ev, i) => (
              <div key={i} className="p-3 rounded border border-slate-200 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-medium text-slate-900">[{i + 1}] {ev.source_name}</span>
                  <span className="text-slate-400">{ev.retrieval_method}</span>
                </div>
                <p className="text-slate-600 mt-1 line-clamp-2">{ev.text}</p>
                <div className="flex gap-3 mt-1 text-slate-400">
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
