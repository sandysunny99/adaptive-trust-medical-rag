import { useState, useEffect } from 'react';
import { Upload, Pill, UserCog, Search, AlertTriangle, X, Cpu, FileText, Download, Check, Clock } from 'lucide-react';
import type { InputMode, PatientContext, PipelineStage, LLMModelInfo, AnalysisResult } from '../types';
import { PipelineProgress } from '../components/PipelineProgress';
import { ResultPanel } from '../components/ResultPanel';
import { MedicationConfirmationPanel } from '../components/MedicationConfirmationPanel';
import { useAnalysis } from '../hooks/useAnalysis';
import { fetchModelCatalog } from '../services/api';
import { exportAsMarkdown, downloadFile } from '../services/exportService';
import { saveAnalysis } from '../services/historyDb';

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

  const addDrugInput = () => setDrugInputs(prev => [...prev, '']);
  const updateDrugInput = (index: number, value: string) => {
    setDrugInputs(prev => prev.map((v, i) => i === index ? value : v));
  };
  const removeDrugInput = (index: number) => {
    if (drugInputs.length > 1) {
      setDrugInputs(prev => prev.filter((_, i) => i !== index));
    }
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setImageFile(e.target.files[0]);
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

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <div className="bg-card rounded-lg border border-border shadow-sm">
        <div className="p-5 border-b border-border">
          <h2 className="text-base font-semibold text-foreground">Medication Safety Analysis</h2>
          <p className="text-sm text-muted-foreground mt-1">
            Upload a prescription image or enter drug names for evidence-grounded safety analysis.
          </p>
        </div>

        {/* Input Mode Tabs */}
        <div className="flex border-b border-border">
          <button
            onClick={() => setInputMode('prescription_image')}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              inputMode === 'prescription_image'
                ? 'border-primary text-primary bg-primary-soft'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Upload size={16} /> Upload Prescription
          </button>
          <button
            onClick={() => setInputMode('direct_drugs')}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              inputMode === 'direct_drugs'
                ? 'border-primary text-primary bg-primary-soft'
                : 'border-transparent text-muted-foreground hover:text-foreground'
            }`}
          >
            <Pill size={16} /> Enter Drug Names
          </button>
        </div>

        <div className="p-5">
          {inputMode === 'prescription_image' && (
            <div className="border-2 border-dashed border-input rounded-lg p-8 text-center hover:border-primary transition-colors cursor-pointer relative">
              <Upload className="mx-auto text-muted-foreground mb-3" size={32} />
              <p className="text-sm text-muted-foreground">
                {imageFile ? imageFile.name : "Drag & drop a prescription image, or click to browse"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">PNG, JPG, or WEBP • Max 5MB</p>
              <input 
                type="file" 
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer" 
                accept="image/jpeg,image/png,image/webp" 
                onChange={handleImageChange}
              />
            </div>
          )}

          {inputMode === 'direct_drugs' && (
            <div className="space-y-3">
              {drugInputs.map((drug, i) => (
                <div key={i} className="flex gap-2">
                  <div className="flex-1 relative">
                    <Pill className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground" size={16} />
                    <input
                      type="text"
                      value={drug}
                      onChange={e => updateDrugInput(i, e.target.value)}
                      placeholder={`Drug name ${i + 1} (e.g., Amoxicillin, Metformin)`}
                      className="w-full pl-10 pr-4 py-2.5 border border-input rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring"
                    />
                  </div>
                  {drugInputs.length > 1 && (
                    <button
                      onClick={() => removeDrugInput(i)}
                      className="px-3 py-2 text-muted-foreground hover:text-destructive transition-colors"
                      aria-label="Remove drug"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              ))}
              <button
                onClick={addDrugInput}
                className="text-sm text-primary hover:text-primary font-medium"
              >
                + Add another drug
              </button>
            </div>
          )}

          {/* Patient Context Toggle */}
          <details className="mt-5">
            <summary className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
              <UserCog size={16} />
              Patient Context (Optional)
            </summary>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <input
                type="number"
                placeholder="Age"
                value={age}
                onChange={e => setAge(e.target.value)}
                className="px-3 py-2 border border-input rounded-lg text-sm"
              />
              <select 
                value={sex}
                onChange={e => setSex(e.target.value)}
                className="px-3 py-2 border border-input rounded-lg text-sm text-muted-foreground"
              >
                <option value="">Sex</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
              <input
                type="text"
                placeholder="Known allergies (comma-separated)"
                value={allergies}
                onChange={e => setAllergies(e.target.value)}
                className="col-span-2 px-3 py-2 border border-input rounded-lg text-sm"
              />
              <input
                type="text"
                placeholder="Known medical conditions"
                value={conditions}
                onChange={e => setConditions(e.target.value)}
                className="col-span-2 px-3 py-2 border border-input rounded-lg text-sm"
              />
              <input
                type="text"
                placeholder="Current other medications"
                value={currentMeds}
                onChange={e => setCurrentMeds(e.target.value)}
                className="col-span-2 px-3 py-2 border border-input rounded-lg text-sm"
              />
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              Only provide information relevant to medication safety. Patient context is optional
              and never inferred from prescriptions.
            </p>
          </details>

          {/* Additional Instructions */}
          <details className="mt-3">
            <summary className="flex items-center gap-2 text-sm font-medium text-foreground cursor-pointer">
              <FileText size={16} />
              Additional Instructions (Optional)
            </summary>
            <div className="mt-3">
              <textarea
                placeholder="Add any specific analysis instructions or questions (e.g., 'Focus on renal dosing adjustments' or 'Check for QT prolongation risk')."
                value={additionalInstructions}
                onChange={e => setAdditionalInstructions(e.target.value)}
                maxLength={2000}
                rows={3}
                className="w-full px-3 py-2 border border-input rounded-lg text-sm resize-y focus:outline-none focus:ring-2 focus:ring-ring focus:border-ring"
              />
              <p className="text-xs text-muted-foreground mt-1">
                Instructions guide analysis focus but cannot override safety gates or evidence requirements.
              </p>
            </div>
          </details>

          {/* Answer-generation Model Selector */}
          <div className="mt-5 p-4 bg-muted rounded-lg border border-border">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Cpu size={16} className="text-primary" />
                <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
                  Answer-generation model
                </span>
              </div>
              <span className="text-[11px] font-medium text-muted-foreground bg-card px-2 py-0.5 rounded border border-border">
                {selectedModelId === 'auto' ? 'Automatic Failover' : 'Direct Selection'}
              </span>
            </div>
            <p className="text-xs text-muted-foreground mb-2">
              Choose the model used to generate your analysis.
            </p>
            <select
              aria-label="Answer-generation model"
              value={selectedModelId}
              onChange={e => setSelectedModelId(e.target.value)}
              disabled={isProcessing || isLoadingModels}
              className="w-full px-3 py-2 border border-input rounded-lg text-sm bg-card focus:outline-none focus:ring-2 focus:ring-ring disabled:opacity-60 disabled:cursor-not-allowed"
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
              <p className="text-[11px] text-warning mt-1">
                {modelCatalogError}
              </p>
            )}
            <p className="text-[11px] text-muted-foreground mt-2">
              {selectedModelId === 'auto'
                ? 'Automatic mode uses the existing provider router and its eligible failover policy.'
                : 'Direct mode routes your query directly to the selected model without silent failover.'}
            </p>
          </div>

          {/* Submit */}
          <div className="mt-5 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-warning">
              <AlertTriangle size={14} />
              <span>Research prototype - does not replace clinical advice</span>
            </div>
            <button
              onClick={handleSubmit}
              disabled={
                isProcessing || 
                (inputMode === 'direct_drugs' && drugInputs.every(d => !d.trim())) ||
                (inputMode === 'prescription_image' && !imageFile)
              }
              className="flex items-center gap-2 px-6 py-2.5 bg-primary text-primary-foreground text-sm font-medium rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Search size={16} />
              Analyze Medications
            </button>
          </div>
        </div>
      </div>

      {/* Pipeline Progress */}
      {currentStage !== 'idle' && (
        <PipelineProgress
          stages={PIPELINE_STAGES}
          currentStage={currentStage}
          updates={stageUpdates}
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
          <AlertTriangle className="text-destructive shrink-0 mt-0.5" size={18} />
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
          <ResultPanel result={result} />
          <div className="flex items-center gap-3 mt-2">
            <button
              onClick={handleSaveToHistory}
              disabled={savedToHistory}
              className={`flex items-center gap-1.5 px-4 py-2 text-sm font-medium rounded-lg border transition-colors cursor-pointer ${
                savedToHistory
                  ? 'bg-success-soft border-success/30 text-success cursor-default'
                  : 'border-input text-foreground hover:bg-muted'
              }`}
            >
              {savedToHistory ? <><Check size={14} /> Saved</> : <><Clock size={14} /> Save to History</>}
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
              <Download size={14} /> Download Report
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
