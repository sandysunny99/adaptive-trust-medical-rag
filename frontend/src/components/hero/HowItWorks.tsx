import { Icons } from '../../ui/icons';
import { IconChip } from '../ui/IconChip';
import { TiltCard } from '../ui/TiltCard';
import { MagicCard } from '../magicui/magic-card';

const STEPS = [
  {
    icon: Icons.stepInput,
    title: 'Input',
    body: 'Type drug names or upload a prescription photo. You confirm what was read before anything is analysed.',
  },
  {
    icon: Icons.stepVerify,
    title: 'Verify evidence',
    body: 'Sources are retrieved, checked for tampering, and scored for trust against the risk of the question.',
  },
  {
    icon: Icons.stepAnswer,
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
                    <IconChip icon={Icon} tone="primary" size="md" />
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
