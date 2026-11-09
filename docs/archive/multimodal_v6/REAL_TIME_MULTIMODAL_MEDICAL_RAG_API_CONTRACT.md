# Live Application API Contract

## Endpoints

### POST /api/v1/analyze
Accepts prescription image or drug names with optional patient context.

**Content-Type**: `multipart/form-data` (image) or `application/json` (text)

#### JSON Input (Direct Drug Names)
```json
{
  "input_mode": "direct_drugs",
  "drug_names": ["amoxicillin", "pantoprazole", "metformin"],
  "patient_context": {
    "age": 65,
    "sex": "male",
    "known_allergies": ["penicillin"],
    "known_conditions": ["type_2_diabetes", "kidney_disease"],
    "current_medications": ["lisinopril"],
    "pregnancy_status": null,
    "breastfeeding": false
  }
}
```

#### Multipart Input (Prescription Image)
```
file: <prescription image>
patient_context: <JSON string>
```

#### Response
```json
{
  "request_id": "uuid",
  "stream_url": "/api/v1/stream/{request_id}"
}
```

### GET /api/v1/stream/{request_id}
SSE stream of pipeline stages.

#### Event Types
```
event: stage_update
data: {"stage": "image_uploaded", "status": "complete", "timestamp": "..."}

event: extraction
data: {"medications": [...], "confidence": {...}}

event: confirmation_required
data: {"medications": [...], "ambiguous": [...]}

event: rxnorm
data: {"entities": [{"raw": "...", "canonical": "...", "rxcui": "...", "status": "MATCHED"}]}

event: retrieval
data: {"evidence_count": 12, "sources": ["pubmed", "openfda"]}

event: trust
data: {"overall": 0.78, "threshold": 0.75, "eligible": true, "factors": {...}}

event: security
data: {"injection": "CLEAN", "poisoning": "CLEAN"}

event: interactions
data: {"pairs": [{"drug_a": "...", "drug_b": "...", "status": "VERIFIED", ...}]}

event: verification
data: {"claims": [...], "grounding_ratio": 0.85, "decision": "release"}

event: answer
data: {"medications": [...], "interactions": [...], "reactions": [...], 
       "warnings": [...], "food_guidance": [...], "patient_considerations": [...],
       "conclusion": {...}, "evidence": [...], "provenance": [...]}

event: abstention
data: {"stage": "evidence_eligibility", "reason": "...", "trust": 0.46, "threshold": 0.75}

event: error
data: {"code": "PROVIDER_FAILURE", "message": "..."}

event: complete
data: {"request_id": "...", "duration_ms": 4200}
```

### POST /api/v1/confirm
Confirms or edits extracted medications after OCR.

```json
{
  "request_id": "uuid",
  "confirmed_medications": [
    {"name": "Amoxicillin", "strength": "500 mg", "form": "Tablet", "frequency": "1-0-1"}
  ]
}
```

## Existing Endpoints (Preserved)
| Method | Path | Purpose |
|--------|------|---------|
| POST | `/query` | Legacy single-query RAG (unchanged) |
| POST | `/ingest` | Document ingestion (unchanged) |
| GET | `/health` | System health (unchanged) |
| GET | `/audit/{session_id}` | Audit log (unchanged) |

## Backend Data Models Mapped to Frontend

### DrugEntity → MedicationCard
```typescript
interface MedicationInfo {
  raw_text: string;
  canonical_name: string | null;
  rxcui: string | null;
  brand_name: string | null;
  formulation: string | null;
  strength: string | null;
  frequency: string | null;
  confidence: number;
  source: 'cache' | 'rxnorm_exact' | 'rxnorm_approx' | 'unresolved';
  status: 'MATCHED' | 'AMBIGUOUS' | 'NOT_FOUND' | 'UNAVAILABLE';
}
```

### TrustScoringResult → TrustPanel
```typescript
interface TrustInfo {
  chunk_id: string;
  risk_class: string;
  trust_score: number;
  threshold: number;
  is_eligible: boolean;
  factors: {
    source_authority: number | null;
    query_relevance: number | null;
    evidence_quality: number | null;
    freshness: number | null;
    consistency: number | null;
    entity_match: number | null;
    population_match: number | null;
    anti_poisoning: number | null;
    anti_injection: number | null;
  };
  missing_factors: string[];
}
```

### VerificationReportV2 → ClaimVerificationPanel
```typescript
interface ClaimInfo {
  claim_id: number;
  text: string;
  support_state: 'SUPPORTED' | 'PARTIALLY_SUPPORTED' | 'CONTRADICTED' | 'UNSUPPORTED' | 'INSUFFICIENT_EVIDENCE' | 'AMBIGUOUS';
  entailment: number;
  contradiction: number;
  citation_present: boolean;
  citation_resolves: boolean;
  best_evidence_chunk: string | null;
  canonical_identity_status: string | null;
}
```

### SecurityDecision → SecurityPanel
```typescript
interface SecurityInfo {
  injection_status: 'ALLOW' | 'FLAG' | 'BLOCK';
  poisoning_status: 'ALLOW' | 'BLOCK';
  injection_markers: string[];
  poisoning_reason: string | null;
}
```
