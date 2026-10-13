import { Icons } from '../ui/icons';
import type { PipelineStage, StageUpdate } from '../types';

interface PipelineProgressProps {
  stages: { key: PipelineStage; label: string }[];
  currentStage: PipelineStage;
  updates: StageUpdate[];
}

function getStageStatus(stageKey: PipelineStage, currentStage: PipelineStage, stages: { key: PipelineStage }[]) {
  const currentIdx = stages.findIndex(s => s.key === currentStage);
  const stageIdx = stages.findIndex(s => s.key === stageKey);
  if (currentStage === 'complete' || currentStage === 'abstained') return 'complete';
  if (currentStage === 'error' || currentStage === 'blocked') {
    if (stageIdx < currentIdx) return 'complete';
    if (stageIdx === currentIdx) return 'failed';
    return 'pending';
  }
  if (stageIdx < currentIdx) return 'complete';
  if (stageIdx === currentIdx) return 'running';
  return 'pending';
}

export function PipelineProgress({ stages, currentStage, updates }: PipelineProgressProps) {
  return (
    <div className="bg-card rounded-lg border border-border shadow-sm p-5">
      <h3 className="text-sm font-semibold text-foreground mb-4">Pipeline Progress</h3>
      <div className="space-y-2">
        {stages.map(({ key, label }) => {
          const status = getStageStatus(key, currentStage, stages);
          const update = updates.find(u => u.stage === key);
          return (
            <div key={key} className="flex items-center gap-3">
              <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                {status === 'complete' && <Icons.pass size={16} className="text-success" />}
                {status === 'running' && <Icons.loading size={16} className="text-primary animate-spin" />}
                {status === 'pending' && <Icons.stepIdle size={16} className="text-muted-foreground" />}
                {status === 'failed' && <Icons.stepFailed size={16} className="text-destructive" />}
              </div>
              <span className={`text-sm ${
                status === 'complete' ? 'text-foreground' :
                status === 'running' ? 'text-primary font-medium' :
                status === 'failed' ? 'text-destructive font-medium' :
                'text-muted-foreground'
              }`}>
                {label}
              </span>
              {update?.duration_ms && (
                <span className="text-xs text-muted-foreground ml-auto">{update.duration_ms}ms</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
