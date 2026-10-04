import { useState, useRef } from 'react';
import { Upload, Pill, UserCog, Search, AlertTriangle, X } from 'lucide-react';
import type { InputMode, PatientContext, PipelineStage } from '../types';
import { PipelineProgress } from '../components/PipelineProgress';
import { ResultPanel } from '../components/ResultPanel';
import { MedicationConfirmationPanel } from '../components/MedicationConfirmationPanel';
import { useAnalysis } from '../hooks/useAnalysis';

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

export function WorkspacePage() {
  const [inputMode, setInputMode] = useState<InputMode>('direct_drugs');
  const [drugInputs, setDrugInputs] = useState<string[]>(['']);
  const [imageFile, setImageFile] = useState<File | null>(null);
  
  // Patient Context state
  const [age, setAge] = useState<string>('');
  const [sex, setSex] = useState<string>('');
  const [allergies, setAllergies] = useState<string>('');
  const [conditions, setConditions] = useState<string>('');
  const [currentMeds, setCurrentMeds] = useState<string>('');

  const { 
    analyze, 
    confirm,
    isProcessing, 
    currentStage, 
    stageUpdates, 
    result, 
    error,
    extractedCandidates
  } = useAnalysis();

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
      imageFile: inputMode === 'prescription_image' ? imageFile : undefined,
      patientContext,
      inputMode
    });
  };

  return (
    <div className="space-y-6">
      {/* Input Section */}
      <div className="bg-white rounded-lg border border-slate-200 shadow-sm">
        <div className="p-5 border-b border-slate-100">
          <h2 className="text-base font-semibold text-slate-900">Medication Safety Analysis</h2>
          <p className="text-sm text-slate-500 mt-1">
            Upload a prescription image or enter drug names for evidence-grounded safety analysis.
          </p>
        </div>

        {/* Input Mode Tabs */}
        <div className="flex border-b border-slate-100">
          <button
            onClick={() => setInputMode('prescription_image')}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              inputMode === 'prescription_image'
                ? 'border-blue-600 text-blue-700 bg-blue-50/50'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Upload size={16} /> Upload Prescription
          </button>
          <button
            onClick={() => setInputMode('direct_drugs')}
            className={`flex items-center gap-2 px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              inputMode === 'direct_drugs'
                ? 'border-blue-600 text-blue-700 bg-blue-50/50'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <Pill size={16} /> Enter Drug Names
          </button>
        </div>

        <div className="p-5">
          {inputMode === 'prescription_image' && (
            <div className="border-2 border-dashed border-slate-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors cursor-pointer relative">
              <Upload className="mx-auto text-slate-400 mb-3" size={32} />
              <p className="text-sm text-slate-600">
                {imageFile ? imageFile.name : "Drag & drop a prescription image, or click to browse"}
              </p>
              <p className="text-xs text-slate-400 mt-1">PNG, JPG, or WEBP • Max 5MB</p>
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
                    <Pill className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                    <input
                      type="text"
                      value={drug}
                      onChange={e => updateDrugInput(i, e.target.value)}
                      placeholder={`Drug name ${i + 1} (e.g., Amoxicillin, Metformin)`}
                      className="w-full pl-10 pr-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                  </div>
                  {drugInputs.length > 1 && (
                    <button
                      onClick={() => removeDrugInput(i)}
                      className="px-3 py-2 text-slate-400 hover:text-red-500 transition-colors"
                      aria-label="Remove drug"
                    >
                      <X size={16} />
                    </button>
                  )}
                </div>
              ))}
              <button
                onClick={addDrugInput}
                className="text-sm text-blue-600 hover:text-blue-800 font-medium"
              >
                + Add another drug
              </button>
            </div>
          )}

          {/* Patient Context Toggle */}
          <details className="mt-5">
            <summary className="flex items-center gap-2 text-sm font-medium text-slate-700 cursor-pointer">
              <UserCog size={16} />
              Patient Context (Optional)
            </summary>
            <div className="mt-3 grid grid-cols-2 gap-3">
              <input
                type="number"
                placeholder="Age"
                value={age}
                onChange={e => setAge(e.target.value)}
                className="px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
              <select 
                value={sex}
                onChange={e => setSex(e.target.value)}
                className="px-3 py-2 border border-slate-300 rounded-lg text-sm text-slate-600"
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
                className="col-span-2 px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
              <input
                type="text"
                placeholder="Known medical conditions"
                value={conditions}
                onChange={e => setConditions(e.target.value)}
                className="col-span-2 px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
              <input
                type="text"
                placeholder="Current other medications"
                value={currentMeds}
                onChange={e => setCurrentMeds(e.target.value)}
                className="col-span-2 px-3 py-2 border border-slate-300 rounded-lg text-sm"
              />
            </div>
            <p className="text-xs text-slate-400 mt-2">
              Only provide information relevant to medication safety. Patient context is optional
              and never inferred from prescriptions.
            </p>
          </details>

          {/* Submit */}
          <div className="mt-5 flex items-center justify-between">
            <div className="flex items-center gap-2 text-xs text-amber-600">
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
              className="flex items-center gap-2 px-6 py-2.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
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
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
          <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
          <div>
            <h3 className="text-sm font-medium text-red-800">Analysis Failed</h3>
            <p className="text-sm text-red-600 mt-1">{error}</p>
          </div>
        </div>
      )}

      {/* Results */}
      {result && currentStage !== 'confirming' && <ResultPanel result={result} />}
    </div>
  );
}
