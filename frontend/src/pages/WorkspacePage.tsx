import { useState, useEffect, useId } from 'react';
import { Icons } from '../ui/icons';
import type { InputMode, PatientContext, PipelineStage, LLMModelInfo, AnalysisResult } from '../types';
import { PipelineProgress } from '../components/PipelineProgress';
import { ResultPanel } from '../components/ResultPanel';
import { MedicationConfirmationPanel } from '../components/MedicationConfirmationPanel';
import { PrescriptionDropzone } from '../components/PrescriptionDropzone';
import { useAnalysis } from '../hooks/useAnalysis';
import { fetchModelCatalog } from '../services/api';
import { exportAsMarkdown, downloadFile } from '../services/exportService';
import { saveAnalysis } from '../services/historyDb';
import { Disclosure } from '../components/ui/Disclosure';
import { SegmentedControl } from '../components/ui/SegmentedControl';
import { cn } from '../utils/cn';

const FIELD_CLASS = 'px-3 py-2 bg-card text-foreground placeholder:text-muted-foreground border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring';

const PIPELINE_STAGES: { key: PipelineStage; label: string }[] = [
  { key: 'uploading', label: 'Input Processing' },
  { key: 'extracting', label: 'Medication Extraction' },
  { key: 'confirming', label: 'User Confirmation' },
  { key: 'normalizing', label: 'RxNorm Canonicalization' },
  { key: 'retrieving', label: 'Evidence Retrieval' },
  { key: 'trust_evaluating', label: 'Trust Evaluation' },
  { key: 'security_checking', label: 'Security Checks' },
  { key: 'relationship_verifying', label: 'Relationship Verification' },
  { key: 'generating', label: 'LLM Analysis' },
  { key: 'claim_verifying', label: 'Claim Verification' },
  { key: 'safety_gating', label: 'Safety Gate' },
];

interface WorkspacePageProps {
  onResultComplete?: (result: AnalysisResult | null) => void;
}

export function WorkspacePage({ onResultComplete }: WorkspacePageProps = {}) {
  const [inputMode, setInputMode] = useState<InputMode>('direct_drugs');
  const [drugInputs, setDrugInputs] = useState<string[]>(['']);
  const [imageFile, setImageFile] = useState<File | null>(null);
  
  // Model selector state
  const [models, setModels] = useState<LLMModelInfo[]>([]);
  const [selectedModelId, setSelectedModelId] = useState<string>('auto');
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(true);
  const [modelCatalogError, setModelCatalogError] = useState<string | null>(null);

  // Additional Instructions state
  const [additionalInstructions, setAdditionalInstructions] = useState<string>('');

  // Patient Context state
  const [age, setAge] = useState<string>('');
  const [sex, setSex] = useState<string>('');
  const [allergies, setAllergies] = useState<string>('');
  const [conditions, setConditions] = useState<string>('');
  const [currentMeds, setCurrentMeds] = useState<string>('');

  useEffect(() => {
    setIsLoadingModels(true);
    fetchModelCatalog()
      .then(catalog => {
        setModels(catalog);
        setModelCatalogError(null);
      })
      .catch(err => {
        console.error('Failed to fetch LLM models:', err);
        setModelCatalogError('Could not load remote model catalog. Defaulting to automatic routing.');
      })
      .finally(() => {
        setIsLoadingModels(false);
      });
  }, []);

  const { 
    analyze, 
    confirm,
    reset,
    isProcessing, 
    currentStage, 
    stageUpdates, 
    result, 
    error,
    extractedCandidates
  } = useAnalysis();

  const [savedToHistory, setSavedToHistory] = useState(false);
  const submitHintId = useId();
  const modelSelectId = useId();

  useEffect(() => {
    if (result && onResultComplete) {
      onResultComplete(result);
    }
    setSavedToHistory(false);
  }, [result, onResultComplete]);

  const handleSaveToHistory = async () => {
    if (!result) return;
    await saveAnalysis({
      id: crypto.randomUUID(),
      timestamp: new Date().toISOString(),
      drugNames: (result.medications || []).map(m => m.canonical_name || m.raw_text),
      inputMode: result.input_mode || inputMode,
      gateDecision: result.gate_decision || 'unknown',
      result,
    });
    setSavedToHistory(true);
  };

  // Clears the result (inputs are kept so they can be adjusted) and returns to the form.
  const startNewAnalysis = () => {
    reset();
    const form = document.querySelector<HTMLElement>('[aria-labelledby="analysis-heading"]');
    form?.scrollIntoView({ block: 'start' });
    form?.querySelector<HTMLElement>('[role="tab"][aria-selected="true"]')?.focus();
  };

  const addDrugInput = () => setDrugInputs(prev => [...prev, '']);
  const updateDrugInput = (index: number, value: string) => {
    setDrugInputs(prev => prev.map((v, i) => i === index ? value : v));
  };
  const removeDrugInput = (index: number) => {
    if (drugInputs.length > 1) {
      setDrugInputs(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleSubmit = async () => {
    const validDrugs = drugInputs.map(d => d.trim()).filter(Boolean);
    
    if (inputMode === 'direct_drugs' && validDrugs.length === 0) return;
    if (inputMode === 'prescription_image' && !imageFile) return;

    let patientContext: PatientContext | null = {};
    if (age || sex || allergies || conditions || currentMeds) {
      if (age) patientContext.age = parseInt(age, 10);
      if (sex) patientContext.sex = sex as 'male' | 'female' | 'other';
      if (allergies) patientContext.known_allergies = allergies.split(',').map(s => s.trim()).filter(Boolean);
      if (conditions) patientContext.known_conditions = conditions.split(',').map(s => s.trim()).filter(Boolean);
      if (currentMeds) patientContext.current_medications = currentMeds.split(',').map(s => s.trim()).filter(Boolean);
      
      if (Object.keys(patientContext).length === 0) {
        patientContext = null;
      }
    }

    await analyze({
      drugNames: inputMode === 'direct_drugs' ? validDrugs : undefined,
      imageFile: inputMode === 'prescription_image' ? (imageFile || undefined) : undefined,
      patientContext,
      additionalInstructions: additionalInstructions.trim() || undefined,
      inputMode,
      llmSelection: selectedModelId === 'auto' ? { mode: 'auto' } : { mode: 'manual', model_id: selectedModelId },
    });
  };

  const hasDrug = drugInputs.some(d => d.trim());
  const canSubmit = !isProcessing && (inputMode === 'direct_drugs' ? hasDrug : Boolean(imageFile));
  const submitHint = isProcessing
    ? null
    : inputMode === 'direct_drugs'
      ? (hasDrug ? null : 'Add at least one drug to analyze.')
      : (imageFile ? null : 'Choose a prescription image to analyze.');

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <section aria-labelledby="analysis-heading" className="bg-card rounded-xl border border-border shadow-sm">
        <div className="p-5 border-b border-border">
          <h2 id="analysis-heading" className="text-base font-semibold text-foreground">Medication Safety Analysis</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Upload a prescription image or enter drug names for evidence-grounded safety analysis.
          </p>
        </div>

        <div className="p-5 space-y-5">
          <SegmentedControl<InputMode>
            ariaLabel="Input method"
            value={inputMode}
            onChange={setInputMode}
            options={[
              { value: 'prescription_image', label: 'Upload Prescription', icon: <Icons.upload size={16} /> },
              { value: 'direct_drugs', label: 'Enter Drug Names', icon: <Icons.enterDrugs size={16} /> },
            ]}
          />

          {inputMode === 'prescription_image' && (
            <PrescriptionDropzone file={imageFile} onFileChange={setImageFile} disabled={isProcessing} />
          )}

          {inputMode === 'direct_drugs' && (
            <div className="space-y-3">
              {drugInputs.map((drug, i) => (
                <div key={i} className="flex gap-2">
                  <div className="flex-1 relative">
                    <Icons.medication className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} aria-hidden="true" />
                    <input
                      type="text"
                      value={drug}
                      onChange={e => updateDrugInput(i, e.target.value)}
                      placeholder={`Drug name ${i + 1} (e.g., Amoxicillin, Metformin)`}
                      aria-label={`Drug name ${i + 1}`}
                      className="w-full pl-10 pr-4 py-2.5 bg-card text-foreground placeholder:text-muted-foreground border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring"
                    />
                  </div>
                  {drugInputs.length > 1 && (
                    <button
                      type="button"
                      onClick={() => removeDrugInput(i)}
                      className="px-3 py-2 rounded-lg text-muted-foreground hover:text-destructive transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      aria-label={`Remove drug ${i + 1}`}
                      title={`Remove drug ${i + 1}`}
                    >
                      <Icons.remove size={16} aria-hidden="true" />
                    </button>
                  )}
                </div>
              ))}
              <button
                type="button"
                onClick={addDrugInput}
                className="rounded text-sm text-primary hover:underline font-medium focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                + Add another drug
              </button>
            </div>
          )}

          <div className="space-y-3">
            <Disclosure title="Patient Context" hint="Optional" icon={<Icons.patientContext size={16} />}>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input
                  type="number"
                  placeholder="Age"
                  aria-label="Age"
                  value={age}
                  onChange={e => setAge(e.target.value)}
                  className={FIELD_CLASS}
                />
                <select
                  aria-label="Sex"
                  value={sex}
                  onChange={e => setSex(e.target.value)}
                  className={FIELD_CLASS}
                >
                  <option value="">Sex</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
                <input
                  type="text"
                  placeholder="Known allergies (comma-separated)"
                  aria-label="Known allergies"
                  value={allergies}
                  onChange={e => setAllergies(e.target.value)}
                  className={`sm:col-span-2 ${FIELD_CLASS}`}
                />
                <input
                  type="text"
                  placeholder="Known medical conditions"
                  aria-label="Known medical conditions"
                  value={conditions}
                  onChange={e => setConditions(e.target.value)}
                  className={`sm:col-span-2 ${FIELD_CLASS}`}
                />
                <input
                  type="text"
                  placeholder="Current other medications"
                  aria-label="Current other medications"
                  value={currentMeds}
                  onChange={e => setCurrentMeds(e.target.value)}
                  className={`sm:col-span-2 ${FIELD_CLASS}`}
                />
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Only provide information relevant to medication safety. Patient context is optional
                and never inferred from prescriptions.
              </p>
            </Disclosure>

            <Disclosure title="Additional Instructions" hint="Optional" icon={<Icons.instructions size={16} />}>
              <textarea
                placeholder="Add any specific analysis instructions or questions (e.g., 'Focus on renal dosing adjustments' or 'Check for QT prolongation risk')."
                aria-label="Additional instructions"
                value={additionalInstructions}
                onChange={e => setAdditionalInstructions(e.target.value)}
                maxLength={2000}
                rows={3}
                className={`w-full resize-y ${FIELD_CLASS}`}
              />
              <p className="text-xs text-muted-foreground mt-1">
                Instructions guide analysis focus but cannot override safety gates or evidence requirements.
              </p>
            </Disclosure>

            <Disclosure title="Advanced settings" icon={<Icons.advancedSettings size={16} />}>
              <label htmlFor={modelSelectId} className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                <Icons.model size={16} className="text-muted-foreground" />
                Answer-generation model
              </label>
              <p className="text-xs text-muted-foreground mt-0.5 mb-2">
                Choose the model used to generate your analysis.
              </p>
              <select
                id={modelSelectId}
                aria-label="Answer-generation model"
                value={selectedModelId}
                onChange={e => setSelectedModelId(e.target.value)}
                disabled={isProcessing || isLoadingModels}
                className={`w-full disabled:opacity-60 disabled:cursor-not-allowed ${FIELD_CLASS}`}
              >
                <option value="auto">
                  {isLoadingModels ? 'Loading model catalog...' : 'Automatic selection (recommended)'}
                </option>
                {models.map(m => (
                  <option key={m.id} value={m.id} disabled={!m.is_available}>
                    {m.name} ({m.provider}){m.is_available ? '' : ' — Not configured'}
                  </option>
                ))}
              </select>
              {modelCatalogError && (
                <p className="text-xs text-warning mt-1">
                  {modelCatalogError}
                </p>
              )}
              {selectedModelId !== 'auto' && (
                <p className="text-xs text-muted-foreground mt-2">
                  Direct mode routes your query directly to the selected model without silent failover.
                </p>
              )}
            </Disclosure>
          </div>

          {/* Submit */}
          <div className="flex sm:justify-end">
            <div className="flex w-full flex-col items-stretch gap-1 sm:w-auto sm:items-end">
              <button
                type="button"
                onClick={handleSubmit}
                disabled={!canSubmit}
                aria-describedby={submitHint ? submitHintId : undefined}
                className={cn(
                  'flex items-center justify-center gap-2 px-6 py-2.5 text-sm font-semibold rounded-lg transition-colors',
                  'focus:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-card',
                  canSubmit
                    ? 'bg-primary text-primary-foreground shadow-sm hover:bg-primary/90 cursor-pointer'
                    : 'bg-muted text-muted-foreground border border-border cursor-not-allowed'
                )}
              >
                {isProcessing
                  ? <Icons.loading size={16} className="animate-spin" aria-hidden="true" />
                  : <Icons.runAnalysis size={16} aria-hidden="true" />}
                {isProcessing ? 'Analyzing…' : 'Analyze Medications'}
              </button>
              {submitHint && (
                <p id={submitHintId} className="text-xs text-muted-foreground sm:text-right">
                  {submitHint}
                </p>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Pipeline Progress */}
      {currentStage !== 'idle' && (
        <PipelineProgress
          stages={PIPELINE_STAGES}
          currentStage={currentStage}
          updates={stageUpdates}
          processingTimeMs={result?.processing_time_ms}
        />
      )}

      {/* Confirmation Panel */}
      {currentStage === 'confirming' && extractedCandidates && extractedCandidates.length > 0 && (
        <MedicationConfirmationPanel 
          candidates={extractedCandidates}
          onConfirm={confirm}
        />
      )}

      {/* Error Message */}
      {error && (
        <div className="bg-destructive-soft border border-destructive/30 rounded-lg p-4 flex items-start gap-3">
          <Icons.error className="text-destructive shrink-0 mt-0.5" size={18} />
          <div className="flex-1">
            <h3 className="text-sm font-medium text-destructive">Analysis Failed</h3>
            <p className="text-sm text-destructive mt-1">{error}</p>
            <button
              onClick={reset}
              className="mt-2 text-sm text-destructive hover:text-destructive font-medium underline"
            >
              ← Back to input
            </button>
          </div>
        </div>
      )}

      {/* Results */}
      {result && currentStage !== 'confirming' && (
        <div className="space-y-4">
          <ResultPanel result={result} showDetails={!isProcessing} />
          <div className="flex flex-wrap items-center gap-3 mt-2">
            <button
              onClick={handleSaveToHistory}
              disabled={savedToHistory}
              className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                savedToHistory
                  ? 'bg-success-soft border-success/30 text-success cursor-default'
                  : 'border-input text-foreground hover:bg-muted'
              }`}
            >
              {savedToHistory ? <><Icons.saved size={14} /> Saved</> : <><Icons.save size={14} /> Save to History</>}
            </button>
            <button
              onClick={() => {
                const md = exportAsMarkdown({
                  id: 'export',
                  timestamp: new Date().toISOString(),
                  drugNames: (result.medications || []).map(m => m.canonical_name || m.raw_text),
                  inputMode: result.input_mode || inputMode,
                  gateDecision: result.gate_decision || 'unknown',
                  result,
                });
                downloadFile(md, `analysis-${Date.now()}.md`, 'text/markdown');
              }}
              className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg border border-input text-foreground hover:bg-muted cursor-pointer"
            >
              <Icons.download size={14} /> Download Report
            </button>
            {!isProcessing && (
              <button
                type="button"
                onClick={startNewAnalysis}
                className="flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg border border-input text-foreground hover:bg-muted cursor-pointer focus:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <Icons.newAnalysis size={14} /> New analysis
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
