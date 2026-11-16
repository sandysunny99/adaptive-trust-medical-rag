import { Icons } from '../ui/icons';
import type { InputMode, PipelineStage, StageUpdate } from '../types';
import { usePrefersReducedMotion } from '../hooks/usePrefersReducedMotion';
import { Disclosure } from './ui/Disclosure';

interface PipelineProgressProps {
  stages: { key: PipelineStage; label: string }[];
  currentStage: PipelineStage;
  updates: StageUpdate[];
  /** `processing_time_ms` from the answer payload, when present. */
  processingTimeMs?: number | null;
  /** Manual entry skips the image-only stages; they are shown as not applicable, not as not run. */
  inputMode?: InputMode;
}

type StepStatus = 'complete' | 'running' | 'pending' | 'failed' | 'skipped' | 'not_applicable';

/** Stages that exist only for an uploaded prescription image. */
const IMAGE_ONLY: ReadonlySet<PipelineStage> = new Set<PipelineStage>(['extracting', 'confirming']);
/** Stages the backend checks inside another stage, which reports for them. */
const REPORTED_BY: Partial<Record<PipelineStage, PipelineStage>> = { relationship_verifying: 'claim_verifying' };
/** Stages the backend reports only after the user confirmed the extracted medications. */
const AFTER_CONFIRMATION: ReadonlySet<PipelineStage> = new Set<PipelineStage>(['uploading', 'normalizing']);

/**
 * User confirmation has no backend update of its own. It is complete only when extraction
 * completed and the backend then went on to the stages that need confirmed medications; a failed
 * or missing extraction can never make it complete.
 */
function confirmationStatus(currentStage: PipelineStage, updates: StageUpdate[]): StepStatus {
  const extraction = updates.find(u => u.stage === 'extracting');
  const ended = currentStage === 'complete' || currentStage === 'abstained' || currentStage === 'error' || currentStage === 'blocked';
  if (!extraction || extraction.status !== 'complete') return ended ? 'skipped' : 'pending';
  if (updates.some(u => AFTER_CONFIRMATION.has(u.stage))) return 'complete';
  if (currentStage === 'confirming') return 'running';
  return ended ? 'skipped' : 'pending';
}

function getStageStatus(
  stageKey: PipelineStage,
  currentStage: PipelineStage,
  updates: StageUpdate[],
  inputMode?: InputMode,
): StepStatus {
  if (inputMode && inputMode !== 'prescription_image' && IMAGE_ONLY.has(stageKey)) return 'not_applicable';
  if (stageKey === 'confirming') return confirmationStatus(currentStage, updates);
  const update = updates.find(u => u.stage === (REPORTED_BY[stageKey] ?? stageKey));
  if (currentStage === 'complete') {
    // An answer is released only after every stage ran; a reported failure still shows.
    return update?.status === 'failed' ? 'failed' : 'complete';
  }
  // An abstention or an error can stop the pipeline early, so each stage's own last
  // update says what happened to it; a stage the backend never reported did not run.
  const stopped = currentStage === 'error' || currentStage === 'blocked';
  if (currentStage === 'abstained' || stopped) {
    if (!update) return 'skipped';
    if (update.status === 'failed') return 'failed';
    if (update.status === 'skipped' || update.status === 'pending') return 'skipped';
    // A stage still running when an error ended the stream was interrupted by it.
    if (update.status === 'running' && stopped) return 'failed';
    return 'complete';
  }
  if (update?.status === 'failed') return 'failed';
  if (update?.status === 'complete') return 'complete';
  if (update?.status === 'running' || stageKey === currentStage) return 'running';
  return 'pending';
}

function formatSeconds(ms: number): string {
  return `${(ms / 1000).toFixed(1)} s`;
}

function StepList({ stages, currentStage, updates, inputMode }: PipelineProgressProps) {
  const reduceMotion = usePrefersReducedMotion();
  return (
    <ol className="space-y-2">
      {stages.map(({ key, label }) => {
        const status = getStageStatus(key, currentStage, updates, inputMode);
        const update = updates.find(u => u.stage === key);
        return (
          <li key={key} className="flex items-center gap-3">
            <span className="flex h-5 w-5 flex-shrink-0 items-center justify-center">
              {status === 'complete' && <Icons.pass size={16} className="text-success" />}
              {status === 'running' && (reduceMotion
                ? <Icons.stepRunningStatic size={16} className="text-primary" />
                : <Icons.loading size={16} className="text-primary animate-spin" />)}
              {status === 'pending' && <Icons.stepIdle size={16} className="text-muted-foreground" />}
              {status === 'failed' && <Icons.stepFailed size={16} className="text-destructive" />}
              {(status === 'skipped' || status === 'not_applicable') && <Icons.stepSkipped size={16} className="text-muted-foreground" />}
            </span>
            <span className={`text-sm ${
              status === 'complete' ? 'text-foreground' :
              status === 'running' ? 'text-primary font-medium' :
              status === 'failed' ? 'text-destructive font-medium' :
              'text-muted-foreground'
            }`}>
              {label}
              {status === 'running' && <span className="sr-only"> (in progress)</span>}
              {status === 'failed' && <span className="sr-only"> (failed)</span>}
            </span>
            {status === 'skipped' && <span className="text-xs text-muted-foreground">Not run</span>}
            {status === 'not_applicable' && <span className="text-xs text-muted-foreground">Not applicable</span>}
            {update?.duration_ms && (
              <span className="text-xs text-muted-foreground ml-auto">{update.duration_ms}ms</span>
            )}
          </li>
        );
      })}
    </ol>
  );
}

/**
 * While running, or if a step failed: the full step list. Once the analysis
 * finished: one summary row ("11 of 11 steps completed · 14.2 s") that expands
 * to the list. The time is the backend's processing_time_ms, omitted if absent.
 */
export function PipelineProgress(props: PipelineProgressProps) {
  const { stages, currentStage, updates, processingTimeMs, inputMode } = props;
  const finished = currentStage === 'complete' || currentStage === 'abstained';

  if (!finished) {
    return (
      <section aria-labelledby="pipeline-heading" className="bg-card rounded-lg border border-border shadow-sm p-5">
        <h3 id="pipeline-heading" className="text-sm font-semibold text-foreground mb-4">Pipeline Progress</h3>
        <StepList {...props} />
      </section>
    );
  }

  const statuses = stages.map(s => getStageStatus(s.key, currentStage, updates, inputMode));
  const done = statuses.filter(st => st === 'complete').length;
  const applicable = statuses.filter(st => st !== 'not_applicable').length;
  const summary = [
    `${done} of ${applicable} steps completed`,
    typeof processingTimeMs === 'number' && Number.isFinite(processingTimeMs) ? formatSeconds(processingTimeMs) : null,
  ].filter(Boolean).join(' · ');

  return (
    <Disclosure
      className="bg-card shadow-sm"
      icon={done === applicable
        ? <Icons.pass size={16} className="text-success" />
        : <Icons.abstained size={16} className="text-muted-foreground" />}
      title="Pipeline Progress"
      hint={summary}
    >
      <StepList {...props} />
    </Disclosure>
  );
}
