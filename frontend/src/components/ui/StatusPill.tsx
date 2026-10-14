import { Icons, type IconComponent } from '../../ui/icons';
import { cn } from '../../utils/cn';
import { TONE_CLASSES, type Tone } from '../../ui/tones';

interface StatusPillProps {
  icon: IconComponent;
  label: string;
  tone: Tone;
  className?: string;
}

/** Icon plus visible text in a tone-tinted pill. The text always carries the meaning. */
export function StatusPill({ icon: Icon, label, tone, className }: StatusPillProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ring-1 ring-inset whitespace-nowrap',
        TONE_CLASSES[tone],
        className
      )}
    >
      <Icon size={14} />
      {label}
    </span>
  );
}

const GATE_STATUS: Record<string, { icon: IconComponent; tone: Tone }> = {
  ALLOW: { icon: Icons.pass, tone: 'success' },
  FLAG: { icon: Icons.caution, tone: 'warning' },
  BLOCK: { icon: Icons.block, tone: 'destructive' },
};

/**
 * ALLOW / FLAG / BLOCK from the backend, shown as returned. A missing value
 * reads PENDING while the analysis runs and NOT RUN once it has ended;
 * anything unrecognised is shown verbatim in a neutral pill.
 */
export function SecurityStatusPill({ status, ended = false }: { status: string | null | undefined; ended?: boolean }) {
  if (!status) {
    return ended
      ? <StatusPill icon={Icons.stepSkipped} label="NOT RUN" tone="muted" />
      : <StatusPill icon={Icons.pending} label="PENDING" tone="muted" />;
  }
  const config = GATE_STATUS[status];
  if (!config) return <StatusPill icon={Icons.pending} label={status} tone="muted" />;
  return <StatusPill icon={config.icon} label={status} tone={config.tone} />;
}

/** Risk tier exactly as returned (R0–R3), in a neutral pill: the tier is not recoloured. */
export function RiskTierPill({ tier }: { tier: string }) {
  return <StatusPill icon={Icons.riskTier} label={tier} tone="muted" className="font-mono" />;
}
