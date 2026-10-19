import { lazy, Suspense } from 'react';
import { Hero } from '../components/hero/Hero';
import { WorkspacePage } from './WorkspacePage';

// Decorative tilt cards pull in `motion`; loading them lazily keeps it off the critical path.
const HowItWorks = lazy(() =>
  import('../components/hero/HowItWorks').then(m => ({ default: m.HowItWorks }))
);

const ANALYSIS_FORM_ID = 'analysis-form';

/** Landing hero + "How it works" + the analysis workspace (form and results). */
export function AnalyzePage() {
  return (
    <div className="space-y-8">
      <Hero targetId={ANALYSIS_FORM_ID} />
      <Suspense fallback={<div className="h-40" aria-hidden="true" />}>
        <HowItWorks />
      </Suspense>
      <div id={ANALYSIS_FORM_ID} tabIndex={-1} className="scroll-mt-32 rounded-xl focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background">
        <WorkspacePage />
      </div>
    </div>
  );
}
