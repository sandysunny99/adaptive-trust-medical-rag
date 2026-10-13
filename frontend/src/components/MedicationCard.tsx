import { Pill, Check, AlertTriangle, HelpCircle, X } from 'lucide-react';
import type { MedicationInfo } from '../types';

interface MedicationCardProps {
  medication: MedicationInfo;
}

const STATUS_CONFIG = {
  MATCHED: { icon: Check, color: 'text-success', bg: 'bg-success-soft', label: 'Verified' },
  AMBIGUOUS: { icon: AlertTriangle, color: 'text-warning', bg: 'bg-warning-soft', label: 'Ambiguous' },
  NOT_FOUND: { icon: X, color: 'text-destructive', bg: 'bg-destructive-soft', label: 'Not Found' },
  UNAVAILABLE: { icon: HelpCircle, color: 'text-muted-foreground', bg: 'bg-muted', label: 'Unavailable' },
} as const;

export function MedicationCard({ medication }: MedicationCardProps) {
  const config = STATUS_CONFIG[medication.status];
  const StatusIcon = config.icon;

  return (
    <div className={`rounded-lg border border-border p-4 ${config.bg}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Pill size={16} className="text-primary" />
          <span className="font-medium text-foreground">
            {medication.canonical_name || medication.raw_text}
          </span>
        </div>
        <div className={`flex items-center gap-1 text-xs font-medium ${config.color}`}>
          <StatusIcon size={14} />
          {config.label}
        </div>
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
