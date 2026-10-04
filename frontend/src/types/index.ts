// ============================================================
// Core Medical RAG Application Types
// ============================================================

export type InputMode = 'prescription_image' | 'direct_drugs' | 'multiple_drugs';

export type PipelineStage =
  | 'idle'
  | 'uploading'
  | 'extracting'
  | 'confirming'
  | 'normalizing'
  | 'retrieving'
  | 'trust_evaluating'
  | 'security_checking'
  | 'relationship_verifying'
  | 'generating'
  | 'claim_verifying'
  | 'safety_gating'
  | 'complete'
  | 'abstained'
  | 'blocked'
  | 'error';

export type RxNormStatus = 'MATCHED' | 'AMBIGUOUS' | 'NOT_FOUND' | 'UNAVAILABLE';

export type ExtractionConfidence = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNCERTAIN';

export type CandidateStatus = 'DETECTED' | 'UNCERTAIN' | 'CONFIRMED' | 'REJECTED' | 'USER_ADDED' | 'EDITED';

export interface MedicationCandidate {
  id: string;
  raw_text: string;
  normalized_text: string | null;
  confidence: ExtractionConfidence;
  status: CandidateStatus;
  source: 'VISION' | 'OCR' | 'USER';
  source_region?: any;
  warnings?: string[];
}

export type SupportState =
  | 'SUPPORTED'
  | 'PARTIALLY_SUPPORTED'
  | 'CONTRADICTED'
  | 'UNSUPPORTED'
  | 'INSUFFICIENT_EVIDENCE'
  | 'AMBIGUOUS';

export type GateDecision = 'release' | 'qualify' | 'abstain';

export type SecurityState = 'ALLOW' | 'FLAG' | 'BLOCK';

export type CanonicalMatchStatus = 'MATCH' | 'MISMATCH' | 'AMBIGUOUS' | 'UNAVAILABLE';

export type EvidenceStatus = 'VERIFIED' | 'LIMITED' | 'UNKNOWN' | 'NOT_ESTABLISHED';

export interface MedicationInfo {
  raw_text: string;
  canonical_name: string | null;
  rxcui: string | null;
  brand_name: string | null;
  formulation: string | null;
  strength: string | null;
  frequency: string | null;
  route: string | null;
  confidence: number;
  source: 'cache' | 'rxnorm_exact' | 'rxnorm_approx' | 'unresolved';
  status: RxNormStatus;
}

export interface PatientContext {
  age?: number;
  sex?: 'male' | 'female' | 'other';
  known_allergies?: string[];
  known_conditions?: string[];
  current_medications?: string[];
  pregnancy_status?: 'pregnant' | 'not_pregnant' | 'unknown';
  breastfeeding?: boolean;
  kidney_impairment?: 'none' | 'mild' | 'moderate' | 'severe';
  liver_impairment?: 'none' | 'mild' | 'moderate' | 'severe';
}

export interface TrustFactors {
  source_authority: number | null;
  query_relevance: number | null;
  evidence_quality: number | null;
  freshness: number | null;
  consistency: number | null;
  entity_match: number | null;
  population_match: number | null;
  anti_poisoning: number | null;
  anti_injection: number | null;
}

export interface TrustInfo {
  overall_score: number;
  threshold: number;
  risk_class: string;
  is_eligible: boolean;
  factors: TrustFactors;
  missing_factors: string[];
}

export interface EvidenceItem {
  chunk_id: string;
  document_id: string;
  source_type: string;
  source_name: string;
  title: string;
  text: string;
  pmid?: string;
  doi?: string;
  url?: string;
  source_authority: number;
  trust_score: number;
  freshness: number;
  retrieval_method: string;
  provenance_status: string;
}

export interface DrugInteraction {
  drug_a: string;
  drug_b: string;
  rxcui_a: string;
  rxcui_b: string;
  interaction_detected: boolean;
  interaction_type: string | null;
  potential_effect: string | null;
  severity: string | null;
  evidence_status: EvidenceStatus;
  relationship_status: CanonicalMatchStatus;
  sources: string[];
}

export interface AdverseDrugReaction {
  drug: string;
  reaction: string;
  severity: 'common' | 'important' | 'serious';
  evidence_level: EvidenceStatus;
  frequency: string | null;
  source: string;
}

export interface FoodGuidance {
  drug: string;
  administration: string;
  food_relationship: 'WITH_FOOD' | 'WITHOUT_FOOD' | 'WITH_OR_WITHOUT' | 'SPECIFIC_TIMING' | 'UNKNOWN' | 'NOT_VERIFIED';
  timing: string | null;
  food_interactions: string[];
  evidence_status: EvidenceStatus;
  source: string | null;
}

export interface PatientConsideration {
  factor: string;
  provided: boolean;
  evidence_found: boolean;
  consideration: string;
  evidence_status: EvidenceStatus;
  source: string | null;
}

export interface ClaimInfo {
  claim_id: number;
  text: string;
  support_state: SupportState;
  entailment: number;
  contradiction: number;
  citation_present: boolean;
  citation_resolves: boolean;
  best_evidence_chunk: string | null;
  canonical_identity_status: CanonicalMatchStatus | null;
}

export interface SecurityInfo {
  injection_status: SecurityState;
  poisoning_status: SecurityState;
  injection_markers: string[];
  poisoning_reason: string | null;
}

export interface ProvenanceStep {
  level: 'source' | 'document' | 'chunk' | 'evidence' | 'claim' | 'answer';
  id: string;
  label: string;
  detail?: string;
}

export interface AnalysisResult {
  request_id: string;
  input_mode: InputMode;
  medications: MedicationInfo[];
  patient_context: PatientContext | null;
  interactions: DrugInteraction[];
  adverse_reactions: AdverseDrugReaction[];
  warnings: string[];
  food_guidance: FoodGuidance[];
  patient_considerations: PatientConsideration[];
  trust: TrustInfo | null;
  security: SecurityInfo | null;
  claims: ClaimInfo[];
  evidence: EvidenceItem[];
  provenance: ProvenanceStep[];
  conclusion: string;
  gate_decision: GateDecision;
  abstention_reason: string | null;
  disclaimer: string;
}

export interface StageUpdate {
  stage: PipelineStage;
  status: 'pending' | 'running' | 'complete' | 'failed' | 'skipped';
  message?: string;
  timestamp: string;
  duration_ms?: number;
  data?: unknown;
}
