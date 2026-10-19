/** Status tones shared by IconChip and StatusPill. */
export type Tone = 'primary' | 'success' | 'warning' | 'destructive' | 'muted';

/** Tinted background (~12%), ring (~20%) and foreground per tone. Shared with StatusPill. */
export const TONE_CLASSES: Record<Tone, string> = {
  primary: 'bg-primary/12 ring-primary/20 text-primary',
  success: 'bg-success/12 ring-success/20 text-success',
  warning: 'bg-warning/12 ring-warning/20 text-warning',
  destructive: 'bg-destructive/12 ring-destructive/20 text-destructive',
  muted: 'bg-muted ring-border text-muted-foreground',
};
