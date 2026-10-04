import { useState, useCallback, useRef, useEffect } from 'react';
import type { 
  InputMode, 
  PatientContext, 
  AnalysisResult, 
  StageUpdate,
  PipelineStage,
  MedicationCandidate
} from '../types';
import { submitAnalysis, submitPrescriptionImage, confirmMedications, connectStream } from '../services/api';

export function useAnalysis() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStage, setCurrentStage] = useState<PipelineStage>('idle');
  const [stageUpdates, setStageUpdates] = useState<StageUpdate[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [extractedCandidates, setExtractedCandidates] = useState<MedicationCandidate[]>([]);
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null);
  
  // Keep track of the active connection
  const disconnectRef = useRef<(() => void) | null>(null);

  const cleanup = useCallback(() => {
    if (disconnectRef.current) {
      disconnectRef.current();
      disconnectRef.current = null;
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return cleanup;
  }, [cleanup]);

  const handleStreamEvent = useCallback((event: string, data: any, existingResult: Partial<AnalysisResult>) => {
    let partialResult = { ...existingResult };
    
    switch (event) {
      case 'stage_update':
        setCurrentStage(data.stage);
        setStageUpdates(prev => {
          const existing = prev.findIndex(u => u.stage === data.stage);
          if (existing >= 0) {
            const next = [...prev];
            next[existing] = data;
            return next;
          }
          return [...prev, data];
        });
        break;

      case 'medication_candidates_extracted':
        setExtractedCandidates(data.candidates || []);
        break;

      case 'confirmation_required':
        setCurrentStage('confirming');
        break;

      case 'rxnorm':
        partialResult = {
          ...partialResult,
          medications: data.entities || []
        };
        setResult(partialResult as AnalysisResult);
        break;

      case 'trust':
        partialResult = {
          ...partialResult,
          trust: data
        };
        setResult(partialResult as AnalysisResult);
        break;
        
      case 'security':
        partialResult = {
          ...partialResult,
          security: data
        };
        setResult(partialResult as AnalysisResult);
        break;
        
      case 'answer':
        // Full answer overrides everything
        partialResult = data;
        setResult(partialResult as AnalysisResult);
        break;
        
      case 'abstention':
        partialResult = {
          ...partialResult,
          gate_decision: 'abstain',
          abstention_reason: data.reason,
          trust: data.trust
        };
        setResult(partialResult as AnalysisResult);
        setCurrentStage('abstained');
        break;

      case 'error':
        setError(data.message || 'Unknown error occurred.');
        setCurrentStage('error');
        setIsProcessing(false);
        cleanup();
        break;
        
      case 'complete':
        setIsProcessing(false);
        cleanup();
        break;
    }
    return partialResult;
  }, [cleanup]);

  const analyze = useCallback(async (
    payload: {
      drugNames?: string[];
      imageFile?: File;
      patientContext?: PatientContext | null;
      inputMode: InputMode;
    }
  ) => {
    cleanup();
    setIsProcessing(true);
    setCurrentStage('uploading');
    setStageUpdates([]);
    setResult(null);
    setError(null);
    setExtractedCandidates([]);
    setCurrentRequestId(null);

    let partialResult: Partial<AnalysisResult> = {
      input_mode: payload.inputMode,
      medications: [],
      interactions: [],
      adverse_reactions: [],
      warnings: [],
      food_guidance: [],
      patient_considerations: [],
      claims: [],
      evidence: [],
      provenance: [],
    };

    try {
      let stream_url = '';
      let req_id = '';
      
      if (payload.inputMode === 'prescription_image' && payload.imageFile) {
        const res = await submitPrescriptionImage(payload.imageFile, payload.patientContext);
        stream_url = res.stream_url;
        req_id = res.request_id;
      } else if (payload.drugNames) {
        const res = await submitAnalysis(payload.drugNames, payload.patientContext, payload.inputMode);
        stream_url = res.stream_url;
        req_id = res.request_id;
      } else {
        throw new Error("Invalid payload for analysis");
      }
      
      setCurrentRequestId(req_id);

      disconnectRef.current = connectStream(
        stream_url,
        (event, data: any) => {
          partialResult = handleStreamEvent(event, data, partialResult);
        },
        (err) => {
          console.error("Stream error", err);
          setError("Connection to analysis stream lost.");
          setCurrentStage('error');
          setIsProcessing(false);
        }
      );
    } catch (err: any) {
      setError(err.message || String(err));
      setCurrentStage('error');
      setIsProcessing(false);
      cleanup();
    }
  }, [cleanup, handleStreamEvent]);

  const confirm = useCallback(async (confirmedNames: string[]) => {
    if (!currentRequestId) return;
    try {
      // Transition from confirming -> running immediately in UI
      setCurrentStage('normalizing'); 
      await confirmMedications(currentRequestId, confirmedNames);
    } catch (err: any) {
      setError(err.message || String(err));
      setCurrentStage('error');
      setIsProcessing(false);
      cleanup();
    }
  }, [currentRequestId, cleanup]);

  return {
    analyze,
    confirm,
    isProcessing,
    currentStage,
    stageUpdates,
    result,
    error,
    extractedCandidates,
    cancel: cleanup
  };
}
