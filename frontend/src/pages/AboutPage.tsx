import { FlaskConical, Shield, Activity, Pill, FileSearch, BarChart3, AlertTriangle } from 'lucide-react';
import { RESEARCH_DISCLAIMER } from '../constants/disclaimer';

const COMPONENTS = [
  { icon: Pill, label: 'RxNorm Alignment', desc: 'Drug entity canonicalization via NLM RxNorm.' },
  { icon: FileSearch, label: 'Multi-Source Retrieval', desc: 'BM25 + Vector + Graph + RRF hybrid retrieval.' },
  { icon: Activity, label: 'Trust-Aware Evidence Control', desc: '9-factor weighted trust scoring with risk-tier thresholds.' },
  { icon: Shield, label: 'Security Defense', desc: 'Prompt injection + retrieval poisoning detection.' },
  { icon: FlaskConical, label: 'Claim Verification', desc: 'PubMedBERT NLI-based claim-level verification.' },
  { icon: BarChart3, label: 'Controlled Abstention', desc: 'Evidence-driven abstention when evidence is insufficient.' },
];

const PIPELINE = [
  'Input processing',
  'Medication extraction (prescription images)',
  'User confirmation of extracted medications',
  'RxNorm canonicalization',
  'Evidence retrieval',
  'Trust evaluation',
  'Security checks',
  'Relationship verification',
  'LLM analysis',
  'Claim verification',
  'Safety gate',
];

const RISK_TIERS = [
  { tier: 'R0', threshold: '0.30' },
  { tier: 'R1', threshold: '0.45' },
  { tier: 'R2', threshold: '0.60' },
  { tier: 'R3', threshold: '0.75' },
];

export function AboutPage() {
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <section aria-labelledby="about-heading" className="bg-card rounded-xl border border-border shadow-sm p-6">
        <h2 id="about-heading" className="text-xl font-semibold text-foreground">About this research prototype</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          Adaptive Trust-Aware Medical RAG is a research testbed for evidence-grounded pharmacology
          questions. It combines multimodal input, real-time retrieval, trust-aware evidence control
          and controlled abstention. It is not an autonomous clinical decision-maker.
        </p>
      </section>

      <section aria-labelledby="disclaimer-heading" className="rounded-xl border border-warning/30 bg-warning-soft p-6">
        <h2 id="disclaimer-heading" className="flex items-center gap-2 text-base font-semibold text-foreground">
          <AlertTriangle size={18} className="text-warning" aria-hidden="true" />
          Disclaimer
        </h2>
        <p className="mt-2 text-sm font-medium text-foreground">{RESEARCH_DISCLAIMER}</p>
        <p className="mt-2 text-sm text-foreground">
          This is an evidence-grounded research prototype. It is NOT an autonomous clinical
          decision-maker and does NOT replace a doctor, pharmacist, or other healthcare professional.
          All outputs are research-grade and require clinical verification. Use synthetic or
          anonymized inputs only; do not enter real patient information.
        </p>
      </section>

      <section aria-labelledby="components-heading">
        <h2 id="components-heading" className="text-base font-semibold text-foreground">Methodology</h2>
        <ul className="mt-3 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {COMPONENTS.map(({ icon: Icon, label, desc }) => (
            <li key={label} className="bg-card rounded-lg border border-border shadow-sm p-4">
              <Icon size={20} className="text-primary mb-2" aria-hidden="true" />
              <h3 className="text-sm font-semibold text-foreground">{label}</h3>
              <p className="text-sm text-muted-foreground mt-1">{desc}</p>
            </li>
          ))}
        </ul>
      </section>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <section aria-labelledby="pipeline-heading" className="bg-card rounded-lg border border-border shadow-sm p-5">
          <h2 id="pipeline-heading" className="text-base font-semibold text-foreground">Pipeline stages</h2>
          <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-foreground">
            {PIPELINE.map(stage => <li key={stage}>{stage}</li>)}
          </ol>
        </section>

        <section aria-labelledby="tiers-heading" className="bg-card rounded-lg border border-border shadow-sm p-5">
          <h2 id="tiers-heading" className="text-base font-semibold text-foreground">Risk tiers and trust thresholds</h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Each question is assigned a risk tier. The system abstains when the trust score is below
            the tier's threshold, when sources of equal authority contradict each other, or when a
            high-risk question lacks verified high-authority evidence.
          </p>
          <table className="mt-3 w-full text-sm">
            <thead>
              <tr className="text-left text-muted-foreground">
                <th scope="col" className="py-1 font-medium">Tier</th>
                <th scope="col" className="py-1 font-medium">Minimum trust score</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border">
              {RISK_TIERS.map(({ tier, threshold }) => (
                <tr key={tier}>
                  <td className="py-1.5 font-mono text-foreground">{tier}</td>
                  <td className="py-1.5 font-mono text-foreground">{threshold}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      </div>
    </div>
  );
}
