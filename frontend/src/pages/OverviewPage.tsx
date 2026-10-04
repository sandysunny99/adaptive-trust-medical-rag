import { FlaskConical, Shield, Activity, Pill, FileSearch, BarChart3 } from 'lucide-react';

export function OverviewPage() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-6">
        <h2 className="text-xl font-bold text-slate-900">Adaptive Trust-Aware Medical RAG</h2>
        <p className="text-sm text-slate-600 mt-2">
          Evidence-grounded pharmacology QA with multimodal input, real-time RAG pipeline,
          trust-aware evidence control, and controlled abstention.
        </p>
        <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <p className="text-xs text-amber-800">
            <strong>Research Prototype</strong> — This system is NOT an autonomous clinical decision-maker.
            All outputs require clinical verification by a qualified healthcare professional.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        {[
          { icon: Pill, label: 'RxNorm Alignment', desc: 'Drug entity canonicalization via NLM RxNorm' },
          { icon: FileSearch, label: 'Multi-Source Retrieval', desc: 'BM25 + Vector + Graph + RRF hybrid retrieval' },
          { icon: Activity, label: 'Trust-Aware Evidence Control', desc: '9-factor weighted trust scoring with risk-tier thresholds' },
          { icon: Shield, label: 'Security Defense', desc: 'Prompt injection + retrieval poisoning detection' },
          { icon: FlaskConical, label: 'Claim Verification', desc: 'PubMedBERT NLI-based claim-level verification' },
          { icon: BarChart3, label: 'Controlled Abstention', desc: 'Evidence-driven abstention when evidence is insufficient' },
        ].map(({ icon: Icon, label, desc }) => (
          <div key={label} className="bg-white rounded-lg border border-slate-200 shadow-sm p-4">
            <Icon size={20} className="text-blue-600 mb-2" />
            <h3 className="text-sm font-semibold text-slate-900">{label}</h3>
            <p className="text-xs text-slate-500 mt-1">{desc}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
