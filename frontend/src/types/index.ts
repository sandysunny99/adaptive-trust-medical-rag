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
  /** The text an independent OCR read in the image that names this candidate (the model's confidence is not evidence). */
  image_text_evidence?: string | null;
}

/**
 * One item of POST /api/v1/analyze/{request_id}/confirm. The backend model
 * (ConfirmedMedicationItem in api/routes/analyze.py) takes objects, never bare names.
 */
export interface ConfirmedMedication {
  name: string;
  status: 'CONFIRMED' | 'EDITED' | 'USER_ADDED';
  source: 'VISION' | 'OCR' | 'USER' | 'USER_EDITED';
  raw_detected_name: string | null;
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
  /** How the drug identity was resolved (for a cache hit, how the entry was first resolved). */
  identity_method?: 'rxnorm_exact' | 'rxnorm_approx' | 'seed_cache' | string;
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
  /** Null when no evidence reached scoring: there is no score, which is not a computed 0. */
  overall_score: number | null;
  score_status?: 'COMPUTED' | 'NO_ELIGIBLE_EVIDENCE';
  threshold: number;
  risk_class: string;
  /** Why the backend chose this risk tier. */
  risk_basis?: string;
  is_eligible: boolean;
  /** Retrieved chunks that named none of the requested medications and were left out. */
  unrelated_excluded?: number;
  /** Retrieved chunks left out because their source identity is not verified. */
  unverified_source_excluded?: number;
  factors: TrustFactors;
  missing_factors: string[];
}

export type SourceLinkStatus = 'VERIFIED' | 'PLACEHOLDER' | 'SHARED' | 'UNVERIFIED' | 'MISSING';
/** Whether the text is known to come from the document it names; only VERIFIED text is evidence. */
export type SourceIdentityStatus = 'VERIFIED' | 'UNVERIFIED' | 'REJECTED_SOURCE_IDENTITY';

/** A retrieved chunk left out before generation because its source identity is not verified. */
export interface ExcludedSource {
  chunk_id: string;
  document_id: string;
  source_type?: string | null;
  source_name?: string | null;
  source_link_status: SourceLinkStatus;
  source_identity_status: SourceIdentityStatus;
  reason: string;
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
  /** Set only when the source URL is verified for this chunk; only then is it a link. */
  url?: string;
  source_link_status?: SourceLinkStatus;
  source_link_note?: string;
  source_authority: number;
  trust_score: number;
  freshness: number;
  retrieval_method: string;
  provenance_status: string;
  source_identity_status?: SourceIdentityStatus;
  /** Title, external ID and version of the verified source document, when known. */
  source_title?: string | null;
  external_id?: string | null;
  source_version?: string | null;
  claim_support_status?: 'SUPPORTS_VERIFIED_CLAIM' | 'NO_VERIFIED_CLAIM' | 'NOT_YET_VERIFIED';
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
  /** Why the claim was withheld at its wording (ACTION_TOO_STRONG, UNSUPPORTED_DETAIL,
   *  NO_REVIEWED_RELATIONSHIP_WORDING, NO_REVIEWED_FOOD_WORDING); absent otherwise. */
  strength_code?: string;
  /** The claimed action, or the unstated extras (QUANTITY, TIMING, CERTAINTY). */
  strength_details?: string[];
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
  /** Chunks excluded before generation for an unverified source identity (abstentions only). */
  excluded_sources?: ExcludedSource[];
  provenance: ProvenanceStep[];
  conclusion: string;
  gate_decision: GateDecision;
  abstention_reason: string | null;
  disclaimer: string;
  /** Total pipeline time reported by the backend in the answer payload. */
  processing_time_ms?: number;
  used_model?: {
    mode: string;
    provider: string;
    model_id: string;
  };
}

export interface StageUpdate {
  stage: PipelineStage;
  status: 'pending' | 'running' | 'complete' | 'failed' | 'skipped';
  message?: string;
  timestamp: string;
  duration_ms?: number;
  data?: unknown;
}

export interface LLMModelInfo {
  id: string;
  provider: string;
  name: string;
  description: string;
  is_available: boolean;
}

export interface LLMSelection {
  mode: 'auto' | 'manual';
  model_id?: string;
  provider?: string;
}
