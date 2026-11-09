# Real-Time Multimodal Medical RAG Application Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     BROWSER (React/TS)                       │
│  Prescription Upload │ Drug Input │ Patient Context          │
│  Live Pipeline View  │ Results    │ Evidence Explorer         │
└──────────────┬──────────────────────────────────────────────┘
               │ SSE / REST
┌──────────────▼──────────────────────────────────────────────┐
│                   FastAPI APPLICATION SERVER                  │
│                                                              │
│  POST /api/v1/analyze     (multipart/JSON)                  │
│  GET  /api/v1/stream/{id} (SSE)                             │
│  GET  /health             (existing)                         │
│  GET  /audit/{session_id} (existing)                         │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌──────────────┐           │
│  │VisionAdapter│  │ RAG Orch.  │  │ LLM Provider │           │
│  │(Groq Qwen) │  │ (existing) │  │ Router       │           │
│  └─────┬──────┘  └─────┬──────┘  └──────┬───────┘           │
│        │               │                │                    │
│  ┌─────▼──────┐  ┌─────▼──────┐  ┌──────▼───────┐           │
│  │Extraction  │  │Trust/Gate  │  │GroqBackend   │           │
│  │Confidence  │  │Security    │  │(text LLM)    │           │
│  └────────────┘  │Verification│  └──────────────┘           │
│                  │Abstention  │                              │
│                  └────────────┘                              │
│                                                              │
│  ┌────────────────────────────────────────────────┐          │
│  │ EXISTING BACKEND SERVICES (unchanged)          │          │
│  │                                                │          │
│  │ DrugNormalizer → RxNormClient → RxNorm API     │          │
│  │ HybridRetrievalEngine (BM25+Vector+Graph+RRF)  │          │
│  │ AdaptiveTrustScorer (9-factor weighted)         │          │
│  │ EvidenceEligibilityGate (pre-generation)        │          │
│  │ ClaimVerifierV2 (PubMedBERT-MNLI NLI)          │          │
│  │ CanonicalRelationshipIdentity                   │          │
│  │ SourceValidator (authority + freshness decay)   │          │
│  │ Sanitizer + InjectionDetector                   │          │
│  │ PoisoningDetector                               │          │
│  │ PubMedAdapter + OpenFDAAdapter + RxNormAdapter  │          │
│  │ EvidenceQueryRouter                             │          │
│  └────────────────────────────────────────────────┘          │
└──────────────────────────────────────────────────────────────┘
```

## Existing Backend Services Inventory

| Service | Module | Key Interface | Status |
|---------|--------|---------------|--------|
| **FastAPI App** | `api/app.py` | `create_app()` factory | ✅ Ready |
| **Query Route** | `api/routes/query.py` | `POST /query` → `RAGRequest` → `RAGResponse` | ✅ Ready |
| **Health Route** | `api/routes/health.py` | `GET /health` | ✅ Ready |
| **Audit Route** | `api/routes/audit.py` | `GET /audit/{session_id}` | ✅ Ready |
| **RAG Orchestrator** | `orchestrator/rag_orchestrator.py` | `AdaptiveTrustRAGOrchestrator.query(RAGRequest)` | ✅ Ready |
| **Drug Normalizer** | `normalization/drug_normalizer.py` | `DrugNormalizer.normalize(str) → DrugEntity` | ✅ Ready |
| **RxNorm Client** | `normalization/drug_normalizer.py` | `RxNormClient.get_rxcui_exact/approximate()` | ✅ Ready |
| **RxNorm Adapter** | `evidence_sources/rxnorm_adapter.py` | `RxNormAdapter.search/fetch/normalize()` | ✅ Ready |
| **Hybrid Retrieval** | `retrieval/hybrid_retrieval.py` | `HybridRetrievalEngine.retrieve()` | ✅ Ready |
| **Trust Scorer** | `trust_scoring/trust_scorer.py` | `AdaptiveTrustScorer.score()` → `TrustScoringResult` | ✅ Ready |
| **Claim Verifier** | `verification/claim_verifier_v2.py` | `ClaimVerifierV2.verify()` → `VerificationReportV2` | ✅ Ready |
| **Canonical Identity** | `verification/canonical_identity.py` | `compare_identity()` → `(CanonicalMatchStatus, str)` | ✅ Ready |
| **Source Validator** | `source_validation/source_validator.py` | `SourceValidator.validate()` → `SourceValidationResult` | ✅ Ready |
| **Sanitizer** | `security/sanitizer.py` | `sanitize_query()` → `SanitizationResult` | ✅ Ready |
| **Injection Detector** | `security_extensions/injection_detector.py` | `PromptInjectionDetector.inspect()` | ✅ Ready |
| **Poisoning Detector** | `security_extensions/poisoning_detector.py` | `RetrievalPoisoningDetector.inspect_provenance()` | ✅ Ready |
| **Groq Backend** | `llm_backend/groq_backend.py` | `GroqBackend.generate(prompt)` (async) | ✅ Ready |
| **Provider Router** | `llm_routing/router.py` | `LLMProviderRouter.generate()` (retry/circuit/failover) | ✅ Ready |
| **Query Router** | `evidence_sources/query_router.py` | `EvidenceQueryRouter.route_query()` | ✅ Ready |
| **PubMed Adapter** | `evidence_sources/pubmed_adapter.py` | `PubMedAdapter.search/fetch/normalize()` | ✅ Ready |
| **OpenFDA Adapter** | `evidence_sources/openfda_adapter.py` | `OpenFDAAdapter.search/fetch/normalize()` | ✅ Ready |

## New Components Required

### 1. Vision/OCR Adapter
- Wraps Groq vision-capable model (e.g., `qwen/qwen3.8-27b`)
- Input: prescription image bytes
- Output: structured medication extraction with confidence scores
- Separated from medical text reasoning LLM

### 2. Live Application Service
- Orchestrates the full multimodal pipeline
- Manages prescription → extraction → confirmation → analysis flow
- Emits SSE events for real-time pipeline progress
- Isolated from research/evaluation mode

### 3. Streaming API
- SSE endpoint for real-time pipeline stage updates
- Each stage emits structured events with status, data, and timing

### 4. Patient Context Service
- Validates and structures optional patient context
- Never infers conditions from prescriptions or drug names
- Passes explicit context to evidence retrieval

## Data Flow

```
INPUT (Image/Text/Multiple Drugs + Optional Patient Context)
  │
  ├─[Image Path]──→ Vision/OCR Model ──→ Extraction + Confidence
  │                                        │
  │                                        ▼
  │                                   User Confirmation
  │                                        │
  ├─[Text Path]───→ Parse Drug Names ──────┤
  │                                        │
  ▼                                        ▼
DrugNormalizer.normalize() ──→ DrugEntity (RxCUI, generic, confidence)
  │
  ▼
HybridRetrievalEngine.retrieve() ──→ ScoredCandidate[]
  │
  ▼
AdaptiveTrustScorer.score() ──→ TrustScoringResult[]
  │
  ▼
EvidenceEligibilityGate.evaluate() ──→ PASS / ABSTAIN
  │
  ├─[ABSTAIN]──→ Controlled Abstention Response
  │
  ├─[PASS]──→ Security Checks (Injection + Poisoning)
  │               │
  │               ▼
  │         CanonicalIdentity.compare_identity()
  │               │
  │               ▼
  │         LLM Generation (Groq text model)
  │               │
  │               ▼
  │         ClaimVerifierV2.verify()
  │               │
  │               ▼
  │         Answer Safety Gate
  │               │
  │               ├─[RELEASE]──→ Verified Result
  │               ├─[QUALIFY]──→ Qualified Result
  │               └─[ABSTAIN]──→ Post-LLM Abstention
  │
  ▼
Structured Response with Provenance
```

## Operating Modes (Isolated)

| Mode | Purpose | Retrieval | LLM | Data |
|------|---------|-----------|-----|------|
| **LIVE** | Real user queries | Live API calls | Real Groq | Transient |
| **RESEARCH** | Controlled experiment | Frozen historical | Frozen config | Immutable artifacts |

These modes MUST NOT share request counting, data storage, or configuration state.
