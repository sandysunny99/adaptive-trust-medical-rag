import { Pill, Check, AlertTriangle, HelpCircle, X } from 'lucide-react';
import type { MedicationInfo } from '../types';

interface MedicationCardProps {
  medication: MedicationInfo;
}

const STATUS_CONFIG = {
  MATCHED: { icon: Check, color: 'text-emerald-600', bg: 'bg-emerald-50', label: 'Verified' },
  AMBIGUOUS: { icon: AlertTriangle, color: 'text-amber-600', bg: 'bg-amber-50', label: 'Ambiguous' },
  NOT_FOUND: { icon: X, color: 'text-red-600', bg: 'bg-red-50', label: 'Not Found' },
  UNAVAILABLE: { icon: HelpCircle, color: 'text-slate-500', bg: 'bg-slate-50', label: 'Unavailable' },
} as const;

export function MedicationCard({ medication }: MedicationCardProps) {
  const config = STATUS_CONFIG[medication.status];
  const StatusIcon = config.icon;

  return (
    <div className={`rounded-lg border border-slate-200 p-4 ${config.bg}`}>
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-2">
          <Pill size={16} className="text-blue-600" />
          <span className="font-medium text-slate-900">
            {medication.canonical_name || medication.raw_text}
          </span>
        </div>
        <div className={`flex items-center gap-1 text-xs font-medium ${config.color}`}>
          <StatusIcon size={14} />
          {config.label}
        </div>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 text-xs text-slate-600">
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
