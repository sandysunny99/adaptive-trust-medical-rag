import { lazy, Suspense } from 'react';
import { usePrefersReducedMotion } from '../../hooks/usePrefersReducedMotion';
import { Icons } from '../../ui/icons';

// The only entry point to the 3D layer; see ParticleField.tsx.
const ParticleField = lazy(() => import('./ParticleField'));

interface HeroProps {
  /** id of the element the CTA scrolls to and focuses. */
  targetId: string;
}

export function Hero({ targetId }: HeroProps) {
  const reduceMotion = usePrefersReducedMotion();

  const startAnalysis = () => {
    const target = document.getElementById(targetId);
    if (!target) return;
    target.scrollIntoView({ behavior: reduceMotion ? 'auto' : 'smooth', block: 'start' });
    target.focus({ preventScroll: true });
  };

  return (
    <section
      aria-labelledby="hero-heading"
      className="relative isolate overflow-hidden rounded-xl border border-border bg-[radial-gradient(ellipse_at_top,var(--hero-from),var(--hero-to)_70%)]"
    >
      {/* Static gradient above is the reduced-motion fallback; particles are layered on top. */}
      {!reduceMotion && (
        <Suspense fallback={null}>
          <ParticleField />
        </Suspense>
      )}
      <div className="relative z-10 mx-auto max-w-3xl px-6 py-14 sm:py-20 text-center">
        <p className="text-xs font-semibold uppercase tracking-widest text-primary">
          Evidence-grounded medication safety
        </p>
        <h2 id="hero-heading" className="mt-3 text-3xl sm:text-5xl font-semibold tracking-tight text-foreground">
          Check medications against retrieved evidence
        </h2>
        <p className="mt-4 text-base sm:text-lg text-muted-foreground">
          Enter drug names or a prescription photo. Every answer is checked against retrieved
          sources, and the system abstains when the evidence isn't strong enough.
        </p>
        <button
          type="button"
          onClick={startAnalysis}
          className="mt-8 inline-flex items-center gap-2 rounded-lg bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground shadow-[0_10px_30px_-10px_var(--accent-glow)] hover:bg-primary/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          Start an analysis
          <Icons.scrollToForm size={16} aria-hidden="true" />
        </button>
      </div>
    </section>
  );
}
