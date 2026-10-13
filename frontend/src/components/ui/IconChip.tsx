import type { IconComponent } from '../../ui/icons';
import { cn } from '../../utils/cn';
import { TONE_CLASSES, type Tone } from '../../ui/tones';

const SIZES = {
  sm: { box: 'h-7 w-7 rounded-md', icon: 16 },
  md: { box: 'h-9 w-9 rounded-lg', icon: 20 },
  lg: { box: 'h-12 w-12 rounded-xl', icon: 24 },
} as const;

interface IconChipProps {
  icon: IconComponent;
  tone?: Tone;
  size?: keyof typeof SIZES;
  className?: string;
}

/** Decorative icon in a tinted rounded square. Always pair it with visible text. */
export function IconChip({ icon: Icon, tone = 'primary', size = 'md', className }: IconChipProps) {
  const s = SIZES[size];
  return (
    <span
      aria-hidden="true"
      className={cn('inline-flex shrink-0 items-center justify-center ring-1 ring-inset', s.box, TONE_CLASSES[tone], className)}
    >
      <Icon size={s.icon} />
    </span>
  );
}
