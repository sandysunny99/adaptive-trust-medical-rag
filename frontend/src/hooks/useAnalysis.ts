import { useState, useCallback, useRef, useEffect } from 'react';
import type { 
  InputMode, 
  PatientContext, 
  AnalysisResult, 
  StageUpdate,
  PipelineStage,
  MedicationCandidate,
  LLMSelection,
  ConfirmedMedication,
} from '../types';
import { submitAnalysis, submitPrescriptionImage, confirmMedications, connectStream, cancelAnalysis } from '../services/api';

export function useAnalysis() {
  const [isProcessing, setIsProcessing] = useState(false);
  const [currentStage, setCurrentStage] = useState<PipelineStage>('idle');
  const [stageUpdates, setStageUpdates] = useState<StageUpdate[]>([]);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  // The input mode of the run in progress, so its stages are labelled for that run, not the form.
  const [runInputMode, setRunInputMode] = useState<InputMode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [extractedCandidates, setExtractedCandidates] = useState<MedicationCandidate[]>([]);
  const [currentRequestId, setCurrentRequestId] = useState<string | null>(null);
  // Abandoned requests whose cancellation the server has not acknowledged. Nothing of them is analysed
  // (that needs a confirmation, never sent), and each ends on the server's confirmation timeout.
  const [unresolvedCancels, setUnresolvedCancels] = useState<string[]>([]);

  // Keep track of the active connection
  const disconnectRef = useRef<(() => void) | null>(null);
  // Each analysis gets a number; a submission or stream event from an older one is ignored, so a
  // slow earlier request can never show its result in place of the current one.
  const generationRef = useRef(0);
  // The cancellation in progress, shared by every control that asks for one.
  const abandoningRef = useRef<Promise<boolean> | null>(null);

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
        // A valid safety outcome, not an error. The backend closes the stream
        // right after it without a 'complete' event, so end the run here or the
        // close is reported as a disconnect.
        // The claims and the eligible evidence they were checked against come with it.
        partialResult = {
          ...partialResult,
          gate_decision: 'abstain',
          abstention_reason: data.reason,
          // The abstention's trust fields win; the trust event's details (factors, exclusions) stay.
          trust: { ...partialResult.trust, ...data.trust },
          claims: data.claims ?? partialResult.claims,
          evidence: data.evidence ?? partialResult.evidence,
          excluded_sources: data.excluded_sources ?? partialResult.excluded_sources,
        };
        setResult(partialResult as AnalysisResult);
        setCurrentStage('abstained');
        setIsProcessing(false);
        cleanup();
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
      additionalInstructions?: string;
      inputMode: InputMode;
      llmSelection?: LLMSelection | null;
    }
  ) => {
    cleanup();
    const generation = ++generationRef.current;
    const isCurrent = () => generation === generationRef.current;
    setIsProcessing(true);
    setCurrentStage('uploading');
    setStageUpdates([]);
    setResult(null);
    setError(null);
    setRunInputMode(payload.inputMode);
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
        const res = await submitPrescriptionImage(payload.imageFile, payload.patientContext, payload.llmSelection, payload.additionalInstructions);
        stream_url = res.stream_url;
        req_id = res.request_id;
      } else if (payload.drugNames) {
        const res = await submitAnalysis(payload.drugNames, payload.patientContext, payload.inputMode, payload.llmSelection, payload.additionalInstructions);
        stream_url = res.stream_url;
        req_id = res.request_id;
      } else {
        throw new Error("Invalid payload for analysis");
      }
      
      if (!isCurrent()) return;  // a newer analysis started while this one was being submitted
      setCurrentRequestId(req_id);

      // Once a terminal event arrives, the stream closing is expected, not a failure.
      let ended = false;
      disconnectRef.current = connectStream(
        stream_url,
        (event, data: any) => {
          if (!isCurrent()) return;
          partialResult = handleStreamEvent(event, data, partialResult);
          if (event === 'abstention' || event === 'complete' || event === 'error') ended = true;
        },
        (err) => {
          if (ended || !isCurrent()) return;
          console.error("Stream error", err);
          setError(prev => prev || "Analysis stream disconnected unexpectedly. Check the backend server status.");
          setCurrentStage('error');
          setIsProcessing(false);
        }
      );
    } catch (err: any) {
      if (!isCurrent()) return;
      setError(err.message || String(err));
      setCurrentStage('error');
      setIsProcessing(false);
      cleanup();
    }
  }, [cleanup, handleStreamEvent]);

  const confirm = useCallback(async (confirmed: ConfirmedMedication[]) => {
    if (!currentRequestId || abandoningRef.current) return;  // a cancel already decided this request
    try {
      // Transition from confirming -> running immediately in UI
      setCurrentStage('normalizing'); 
      await confirmMedications(currentRequestId, confirmed);
    } catch (err: any) {
      setError(err.message || String(err));
      setCurrentStage('error');
      setIsProcessing(false);
      cleanup();
    }
  }, [currentRequestId, cleanup]);

  const reset = useCallback(() => {
    generationRef.current++;
    cleanup();
    setIsProcessing(false);
    setCurrentStage('idle');
    setStageUpdates([]);
    setResult(null);
    setError(null);
    setExtractedCandidates([]);
    setCurrentRequestId(null);
    setRunInputMode(null);
  }, [cleanup]);

  // Asks the server to end an abandoned request. 'cancelled' and 'already_ended' both mean it no longer
  // waits there. Without such an answer the outcome is unknown: the request stays listed for a retry.
  const sendCancel = useCallback(async (requestId: string) => {
    try {
      await cancelAnalysis(requestId);
      setUnresolvedCancels(prev => prev.filter(id => id !== requestId));
      return true;
    } catch (err) {
      if (import.meta.env.DEV) console.warn('Cancel failed', err);
      setUnresolvedCancels(prev => (prev.includes(requestId) ? prev : [...prev, requestId]));
      return false;
    }
  }, []);

  // Abandons the image request, then returns the page to the form. Its events are ignored from the
  // first click, whatever the server answers, and every caller shares one cancellation. Resolves to
  // whether the server acknowledged it.
  const abandon = useCallback((): Promise<boolean> => {
    if (abandoningRef.current) return abandoningRef.current;
    const requestId = currentRequestId;
    generationRef.current++;
    abandoningRef.current = (async () => {
      const acknowledged = requestId ? await sendCancel(requestId) : true;
      reset();
      return acknowledged;
    })().finally(() => { abandoningRef.current = null; });
    return abandoningRef.current;
  }, [currentRequestId, reset, sendCancel]);

  // An image request can be abandoned from the moment it has an ID until its medications are confirmed
  // (the server refuses a cancel after that).
  const abandonable = runInputMode === 'prescription_image' && currentRequestId !== null
    && (currentStage === 'uploading' || currentStage === 'extracting' || currentStage === 'confirming');

  // Sends the unacknowledged cancellations again; resolves to whether all are now acknowledged.
  const retryCancels = useCallback(async () => {
    const results = await Promise.all(unresolvedCancels.map(sendCancel));
    return results.every(Boolean);
  }, [unresolvedCancels, sendCancel]);

  return {
    analyze,
    confirm,
    reset,
    abandon,
    abandonable,
    unresolvedCancels,
    retryCancels,
    isProcessing,
    currentStage,
    stageUpdates,
    result,
    error,
    extractedCandidates,
    runInputMode,
    cancel: cleanup
  };
}
