import { Check, Loader2, Circle, AlertCircle } from 'lucide-react';
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
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
      <h3 className="text-sm font-semibold text-slate-900 mb-4">Pipeline Progress</h3>
      <div className="space-y-2">
        {stages.map(({ key, label }) => {
          const status = getStageStatus(key, currentStage, stages);
          const update = updates.find(u => u.stage === key);
          return (
            <div key={key} className="flex items-center gap-3">
              <div className="flex-shrink-0 w-5 h-5 flex items-center justify-center">
                {status === 'complete' && <Check size={16} className="text-emerald-600" />}
                {status === 'running' && <Loader2 size={16} className="text-blue-600 animate-spin" />}
                {status === 'pending' && <Circle size={16} className="text-slate-300" />}
                {status === 'failed' && <AlertCircle size={16} className="text-red-500" />}
              </div>
              <span className={`text-sm ${
                status === 'complete' ? 'text-slate-900' :
                status === 'running' ? 'text-blue-700 font-medium' :
                status === 'failed' ? 'text-red-600 font-medium' :
                'text-slate-400'
              }`}>
                {label}
              </span>
              {update?.duration_ms && (
                <span className="text-xs text-slate-400 ml-auto">{update.duration_ms}ms</span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
