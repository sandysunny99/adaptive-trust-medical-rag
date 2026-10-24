import { Icons, type IconComponent } from '../ui/icons';
import { StatusPill } from './ui/StatusPill';
import type { Tone } from '../ui/tones';
import type { MedicationInfo } from '../types';

interface MedicationCardProps {
  medication: MedicationInfo;
}

const STATUS_CONFIG: Record<MedicationInfo['status'], { icon: IconComponent; tone: Tone; bg: string; label: string }> = {
  // Drug identity only (an RxCUI was resolved); it does not verify any interaction or evidence.
  MATCHED: { icon: Icons.pass, tone: 'success', bg: 'bg-success-soft', label: 'Identity resolved' },
  AMBIGUOUS: { icon: Icons.caution, tone: 'warning', bg: 'bg-warning-soft', label: 'Ambiguous' },
  NOT_FOUND: { icon: Icons.unknown, tone: 'destructive', bg: 'bg-destructive-soft', label: 'Not Found' },
  UNAVAILABLE: { icon: Icons.pending, tone: 'muted', bg: 'bg-muted', label: 'Unavailable' },
};

const METHOD_LABELS: Record<string, string> = {
  rxnorm_exact: 'RxNorm exact match',
  rxnorm_approx: 'RxNorm approximate match',
  seed_cache: 'Curated local mapping',
};

/** The identity resolution method; a cache hit names how its entry was first resolved. */
function methodLabel(medication: MedicationInfo): string {
  const method = medication.identity_method ?? medication.source;
  const label = METHOD_LABELS[method] ?? method;
  return medication.source === 'cache' && method !== 'seed_cache' ? `${label} (cached)` : label;
}

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
        <div>Identity method: {methodLabel(medication)}</div>
      </div>
      {medication.status === 'MATCHED' && (
        <p className="mt-2 text-[11px] text-muted-foreground">
          Drug identity only. Interactions and evidence are verified separately below.
        </p>
      )}
    </div>
  );
}
