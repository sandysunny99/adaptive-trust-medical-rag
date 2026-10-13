import { ClipboardList, FileSearch, ShieldCheck } from 'lucide-react';
import { TiltCard } from '../ui/TiltCard';
import { MagicCard } from '../magicui/magic-card';

const STEPS = [
  {
    icon: ClipboardList,
    title: 'Input',
    body: 'Type drug names or upload a prescription photo. You confirm what was read before anything is analysed.',
  },
  {
    icon: FileSearch,
    title: 'Verify evidence',
    body: 'Sources are retrieved, checked for tampering, and scored for trust against the risk of the question.',
  },
  {
    icon: ShieldCheck,
    title: 'Safety-checked answer',
    body: 'Each claim is checked against the sources. If the evidence is too weak, the system says so instead of guessing.',
  },
];

export function HowItWorks() {
  return (
    <section aria-labelledby="how-heading">
      <h2 id="how-heading" className="text-sm font-semibold text-foreground">How it works</h2>
      <ol className="mt-3 grid gap-4 md:grid-cols-3">
        {STEPS.map(({ icon: Icon, title, body }, i) => (
          <li key={title}>
            <TiltCard>
              <MagicCard className="h-full">
                <div className="p-5">
                  <div className="flex items-center gap-3">
                    <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary-soft text-primary">
                      <Icon size={18} aria-hidden="true" />
                    </span>
                    <span className="text-xs font-medium text-muted-foreground">Step {i + 1}</span>
                  </div>
                  <h3 className="mt-3 text-sm font-semibold text-foreground">{title}</h3>
                  <p className="mt-1 text-sm text-muted-foreground">{body}</p>
                </div>
              </MagicCard>
            </TiltCard>
          </li>
        ))}
      </ol>
    </section>
  );
}
