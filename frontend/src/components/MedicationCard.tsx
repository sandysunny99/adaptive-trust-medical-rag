import { Icons, type IconComponent } from '../ui/icons';
import { StatusPill } from './ui/StatusPill';
import type { Tone } from '../ui/tones';
import type { MedicationInfo } from '../types';

interface MedicationCardProps {
  medication: MedicationInfo;
}

const STATUS_CONFIG: Record<MedicationInfo['status'], { icon: IconComponent; tone: Tone; bg: string; label: string }> = {
  MATCHED: { icon: Icons.pass, tone: 'success', bg: 'bg-success-soft', label: 'Verified' },
  AMBIGUOUS: { icon: Icons.caution, tone: 'warning', bg: 'bg-warning-soft', label: 'Ambiguous' },
  NOT_FOUND: { icon: Icons.unknown, tone: 'destructive', bg: 'bg-destructive-soft', label: 'Not Found' },
  UNAVAILABLE: { icon: Icons.pending, tone: 'muted', bg: 'bg-muted', label: 'Unavailable' },
};

export function MedicationCard({ medication }: MedicationCardProps) {
  const config = STATUS_CONFIG[medication.status];

  return (
    <div className={`rounded-lg border border-border p-4 ${config.bg}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Icons.medication size={20} className="text-primary" />
          <span className="font-medium text-foreground">
            {medication.canonical_name || medication.raw_text}
          </span>
        </div>
        <StatusPill icon={config.icon} label={config.label} tone={config.tone} />
      </div>
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-muted-foreground">
        {medication.rxcui && <div>RxCUI: <span className="font-mono">{medication.rxcui}</span></div>}
        {medication.strength && <div>Strength: {medication.strength}</div>}
        {medication.formulation && <div>Form: {medication.formulation}</div>}
        {medication.frequency && <div>Frequency: {medication.frequency}</div>}
        {medication.route && <div>Route: {medication.route}</div>}
        <div>Source: {medication.source}</div>
      </div>
    </div>
  );
}
