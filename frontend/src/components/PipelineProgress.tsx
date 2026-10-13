import { Icons } from '../ui/icons';
import type { PipelineStage, StageUpdate } from '../types';
import { usePrefersReducedMotion } from '../hooks/usePrefersReducedMotion';
import { Disclosure } from './ui/Disclosure';

interface PipelineProgressProps {
  stages: { key: PipelineStage; label: string }[];
  currentStage: PipelineStage;
  updates: StageUpdate[];
  /** `processing_time_ms` from the answer payload, when present. */
  processingTimeMs?: number | null;
}

type StepStatus = 'complete' | 'running' | 'pending' | 'failed' | 'skipped';

function getStageStatus(
  stageKey: PipelineStage,
  currentStage: PipelineStage,
  stages: { key: PipelineStage }[],
  updates: StageUpdate[],
): StepStatus {
  const currentIdx = stages.findIndex(s => s.key === currentStage);
  const stageIdx = stages.findIndex(s => s.key === stageKey);
  if (currentStage === 'complete') return 'complete';
  // An abstention can stop the pipeline early; only stages the backend reported actually ran.
  if (currentStage === 'abstained') {
    const ran = updates.some(u => u.stage === stageKey)
      || (stageKey === 'confirming' && updates.some(u => u.stage === 'extracting'));
    return ran ? 'complete' : 'skipped';
  }
  if (currentStage === 'error' || currentStage === 'blocked') {
    if (stageIdx < currentIdx) return 'complete';
    if (stageIdx === currentIdx) return 'failed';
    return 'pending';
  }
  if (stageIdx < currentIdx) return 'complete';
  if (stageIdx === currentIdx) return 'running';
  return 'pending';
}

function formatSeconds(ms: number): string {
  return `${(ms / 1000).toFixed(1)} s`;
}

function StepList({ stages, currentStage, updates }: PipelineProgressProps) {
  const reduceMotion = usePrefersReducedMotion();
  return (
    <ol className="space-y-2">
      {stages.map(({ key, label }) => {
        const status = getStageStatus(key, currentStage, stages, updates);
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
              {status === 'skipped' && <Icons.stepSkipped size={16} className="text-muted-foreground" />}
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
  const { stages, currentStage, updates, processingTimeMs } = props;
  const finished = currentStage === 'complete' || currentStage === 'abstained';

  if (!finished) {
    return (
      <section aria-labelledby="pipeline-heading" className="bg-card rounded-lg border border-border shadow-sm p-5">
        <h3 id="pipeline-heading" className="text-sm font-semibold text-foreground mb-4">Pipeline Progress</h3>
        <StepList {...props} />
      </section>
    );
  }

  const done = stages.filter(s => getStageStatus(s.key, currentStage, stages, updates) === 'complete').length;
  const summary = [
    `${done} of ${stages.length} steps completed`,
    typeof processingTimeMs === 'number' && Number.isFinite(processingTimeMs) ? formatSeconds(processingTimeMs) : null,
  ].filter(Boolean).join(' · ');

  return (
    <Disclosure
      className="bg-card shadow-sm"
      icon={done === stages.length
        ? <Icons.pass size={16} className="text-success" />
        : <Icons.abstained size={16} className="text-muted-foreground" />}
      title="Pipeline Progress"
      hint={summary}
    >
      <StepList {...props} />
    </Disclosure>
  );
}
