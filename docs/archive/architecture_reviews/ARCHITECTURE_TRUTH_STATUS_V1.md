# ARCHITECTURE_TRUTH_STATUS_V1

**Audit Date:** 2026-10-03  
**Audit Method:** Repository forensic inspection (file-by-file, line-by-line code reading)  
**Audit Principle:** Every status is derived from actual code, test, and experiment evidence. No hard-coded PASS.

---

## Status Taxonomy

| Level | Meaning |
|---|---|
| CONCEPTUAL | Mentioned in docs only, no implementation code |
| PLANNED | Design exists, implementation not started |
| CODE_PRESENT | Code exists but never called |
| IMPLEMENTED | Code exists and is called from the main pipeline |
| UNIT_TESTED | Has dedicated unit tests |
| MOCK_TRANSPORT_TESTED | Tests mock external calls (HTTP, DB) |
| INTEGRATION_TESTED | Called through multi-component integration tests |
| OFFLINE_EXECUTED | Executed in real experiment (e.g., Gate 5) without live external APIs |
| LIVE_EXECUTED | Real external HTTP/API call made and response captured |
| E2E_EXECUTED | Full end-to-end with real LLM generation verified |
| FROZEN | Artifact is locked and must not be modified |
| BLOCKED | Cannot proceed without a dependency being resolved |
| LEGACY | Old code superseded by newer implementation |
| DEPRECATED | Explicitly marked for removal |

---

## Evidence Acquisition Model

> **CRITICAL FINDING**: The system operates as a **local-corpus RAG pipeline**. At runtime, evidence is retrieved **entirely from an in-memory 5-document snapshot** loaded from `data/evidence/manifest.json`. No external API (NCBI, Europe PMC, openFDA, ClinicalTrials.gov) is called at query-time.

| Question | Answer | Evidence |
|---|---|---|
| Does orchestrator.query() call external APIs? | **NO** | `rag_orchestrator.py` L474: calls `self._retrieval.retrieve()` which runs in-memory BM25/Vector/Graph |
| Does HybridRetrievalEngine call external APIs? | **NO** | `hybrid_retrieval.py` L404-412: all three retrievers operate on `self._corpus` in memory |
| Are API adapters implemented? | **YES** (4 of 5) | PubMed, Europe PMC, openFDA, RxNorm adapters exist with httpx client code |
| Are API adapters connected to the orchestrator? | **NO** | Adapters are not instantiated by the orchestrator or retrieval engine |
| Were live HTTP requests ever made? | **NO** | No request logs, VCR cassettes, or HTTP traces found |
| Is the frozen corpus the current benchmark source? | **YES** | `data/evidence/manifest.json` (5 documents, SHA-256 recorded) |

```text
LIVE_SOURCE_QUERY = NO
FROZEN_EVIDENCE_SNAPSHOT = YES
BOTH = NO (adapters exist but are disconnected from runtime)
```

---

## Component Status Matrix

### Core Pipeline

| Component | Module | Status | Execution Level | Gate 5 | Evidence |
|---|---|---|---|---|---|
| RAG Orchestrator | `rag_orchestrator.py` (767 lines) | IMPLEMENTED | OFFLINE_EXECUTED | ✅ 92 runs | Full query() path traced |
| Input Sanitizer | `sanitizer.py` | IMPLEMENTED | OFFLINE_EXECUTED | ✅ | Called at L441 |
| Risk Classifier | `trust_scorer.py` L356-385 | IMPLEMENTED | OFFLINE_EXECUTED | ✅ | Keyword-based R0-R3 |
| Drug Normalizer | `drug_normalizer.py` (250 lines) | MOCK_TRANSPORT_TESTED | NOT_EXECUTED (live) | ❌ | Cache-first, API fallback never triggered |
| Hybrid Retrieval | `hybrid_retrieval.py` | INTEGRATION_TESTED | OFFLINE_EXECUTED | ✅ | BM25+Vector+Graph+RRF |
| Trust Scorer | `trust_scorer.py` (386 lines) | INTEGRATION_TESTED | OFFLINE_EXECUTED | ✅ | 9-factor weighted formula |
| Eligibility Gate | `rag_orchestrator.py` L524-565 | INTEGRATION_TESTED | OFFLINE_EXECUTED | ✅ | Threshold-based gating |
| Answer Safety Gate | `claim_verifier.py` (609 lines) | INTEGRATION_TESTED | OFFLINE_EXECUTED | ✅ | 5-stage verification |
| Controlled Abstention | `rag_orchestrator.py` L719-752 | IMPLEMENTED | OFFLINE_EXECUTED | ✅ | Hard safety path |

### API Source Adapters

| API | Adapter | File | Status | Live HTTP | Orchestrator Connected |
|---|---|---|---|---|---|
| RxNorm | RxNormClient + RxNormAdapter | `drug_normalizer.py`, `rxnorm_adapter.py` | MOCK_TRANSPORT_TESTED | ❌ NO | ❌ (cache fallback) |
| NCBI/PubMed | PubMedAdapter | `pubmed_adapter.py` L25-246 | MOCK_TRANSPORT_TESTED | ❌ NO | ❌ |
| Europe PMC | EuropePMCAdapter | `europepmc_adapter.py` L24-206 | MOCK_TRANSPORT_TESTED | ❌ NO | ❌ |
| openFDA | OpenFDAAdapter | `openfda_adapter.py` L24-226 | MOCK_TRANSPORT_TESTED | ❌ NO | ❌ |
| ClinicalTrials.gov | *none* | — | CONCEPTUAL | ❌ NO | ❌ |

### Security Guardrails

| Control | Module | Status | Orchestrator Called | Gate 5 | Generative E2E |
|---|---|---|---|---|---|
| Prompt Injection | `injection_detector.py` | INTEGRATION_TESTED | ✅ L425, L540 | ✅ | ❌ |
| Retrieval Poisoning | `poisoning_detector.py` | INTEGRATION_TESTED | ✅ L492 | ✅ | ❌ |
| Integrity / SHA-256 | `integrity_validator.py` | INTEGRATION_TESTED | ✅ L538-539 | ✅ | ❌ |
| Relationship Grounding | `relationship_grounding_v2.py` | INTEGRATION_TESTED | ✅ L530-537 | ✅ | ❌ |
| Contradiction Detection | `claim_verifier.py` (Stage 4) | IMPLEMENTED | ✅ (within ASG) | ✅ | ❌ |
| Authorization Boundary | `boundary_enforcer.py` | IMPLEMENTED | ✅ L603-608 | ✅ | ❌ |

### Verification Layer

| Component | Module | Status | Orchestrator Called | Evidence |
|---|---|---|---|---|
| AnswerSafetyGate | `claim_verifier.py` L659-660 | INTEGRATION_TESTED | ✅ `safety_gate.verify()` | 5-stage: decompose → align → cite → contradict → decide |
| Claim Decomposition | `claim_verifier.py` (Stage 1) | IMPLEMENTED | ✅ (within ASG) | Sentence splitter + drug extractor |
| Citation Integrity | `claim_verifier.py` (Stage 3) | IMPLEMENTED | ✅ (within ASG) | [Source N] reference check |
| Contradiction Detection | `claim_verifier.py` (Stage 4) | IMPLEMENTED | ✅ (within ASG) | Heuristic NLI patterns |

> **Previous audit error corrected:** AnswerSafetyGate was listed as "UNVERIFIED_COMPONENT" but is actually imported (L60-65) and called (L659-660) in the orchestrator.

### LLM Provider Adapter

| Provider | Module | Status | Live Transport | Live Model | Structured Output |
|---|---|---|---|---|---|
| Groq | `pilot_adapter.py` | MOCK_TRANSPORT_TESTED | ❌ | ❌ | ❌ |
| Cloudflare | `pilot_adapter.py` | MOCK_TRANSPORT_TESTED | ❌ | ❌ | ❌ |
| Hugging Face | `pilot_adapter.py` | MOCK_TRANSPORT_TESTED | ❌ | ❌ | ❌ |
| FreeLLMAPI | `pilot_adapter.py` | MOCK_TRANSPORT_TESTED | ❌ | ❌ | ❌ |

### Track A Schema & Prompt

| Artifact | Status | Hash Verified | Deterministic Tests |
|---|---|---|---|
| Schema (21 fields) | FROZEN | ✅ | 28/28 PASS |
| Adjudication Prompt V2 | FROZEN | ✅ | 21 fields explicitly listed |
| System Prompt V2 | FROZEN | ✅ | — |
| Challenge Prompt V2 | FROZEN | ✅ | — |

### Cognee

| Aspect | Status | Evidence |
|---|---|---|
| CogneeAdapter | INTEGRATION_TESTED | `cognee_adapter.py` with add/cognify/search |
| EvidenceMapper | INTEGRATION_TESTED | Maps Cognee output → EvidenceCandidate |
| POC Backend | AIOSQLite + LanceDB | Verified in security POC |
| Full Medical Benchmark | NOT_EXECUTED | POC ≠ full benchmark |
| Neo4j | CONCEPTUAL | Not connected |
| Qdrant | CONCEPTUAL | Not connected |

---

## Trust Layer: MISSING ≠ ZERO Audit

> **CRITICAL FINDING:** `query_relevance` and `evidence_quality` silently default to 0.0 in the orchestrator.

| Factor | TrustFactorScores Default | Orchestrator Populates? | Behavior When Missing | Impact (R1 weights) |
|---|---|---|---|---|
| source_authority | 0.0 | ✅ `cand.source_authority` | POPULATED | — |
| query_relevance | **0.0** | ❌ NOT SET | **MISSING → ZERO** | **Loses 0.20** |
| evidence_quality | **0.0** | ❌ NOT SET | **MISSING → ZERO** | **Loses 0.15** |
| freshness | 1.0 | ✅ metadata or 0.8 fallback | POPULATED_WITH_FALLBACK | — |
| consistency | 1.0 | ✅ `1.0 - poisoning_score` | POPULATED | — |
| entity_match | 0.0 | ✅ keyword match 1.0/0.5 | POPULATED | — |
| population_match | **1.0** | ❌ NOT SET | **MISSING → OPTIMISTIC (1.0)** | Small (0.05 weight) |
| anti_poisoning | 1.0 | ✅ `1.0 - poisoning_score` | POPULATED | — |
| anti_injection | 1.0 | ⚠️ `1.0 - poisoning_score` | **POPULATED INCORRECTLY** (uses poisoning, not injection) | 0.05 weight |

**Maximum achievable trust score under R1 with missing query_relevance and evidence_quality:**
- Max = 1.0 − 0.20 (query_relevance×0) − 0.15 (evidence_quality×0) = **0.65**
- R1 threshold = 0.45 → candidates CAN pass, but score is artificially deflated

---

## Current vs Conceptual Components

### CURRENT_RUNTIME_COMPONENTS
- RAGOrchestrator, HybridRetrievalEngine (BM25+Vector+Graph+RRF)
- AdaptiveTrustScorer, EvidenceEligibilityGate
- PromptInjectionDetector, RetrievalPoisoningDetector, IntegrityValidator
- RelationshipGrounding V2, AnswerSafetyGate
- LLMProviderAdapter (mock transport only), Frozen Evidence Corpus 2.0.0
- CogneeAdapter/EvidenceMapper (POC backend)

### CONCEPTUAL_COMPONENTS
- FastAPI service layer, Neo4j, Qdrant
- Live API evidence acquisition at query-time
- ClinicalTrials.gov adapter
- Production deployment infrastructure

### LEGACY_COMPONENTS
- BaseAdapterMock, SimpleEmbeddingModel (7-word toy)
- Precomputed/memory-only Cognee cache

---

## Contradictions Found and Resolved

| # | Contradiction | Resolution |
|---|---|---|
| 1 | Previous audit: `LIVE_SOURCE_QUERY = YES` | **Corrected to NO.** URL in code ≠ live API call. Orchestrator retrieves from frozen corpus. |
| 2 | Previous audit: `AnswerSafetyGate = UNVERIFIED` | **Corrected.** ASG is imported (L60-65) and called (L659-660) in orchestrator. |
| 3 | Previous audit: All audits = unconditional `PASS` | **Corrected.** Each status now backed by file/line/experiment evidence. |
| 4 | Previous audit: `NCBI/PMC/FDA = PLANNED/IMPLEMENTED` | **Resolved to MOCK_TRANSPORT_TESTED.** Adapters exist with snapshot-mode tests but no live HTTP. |
| 5 | `anti_injection` = `1.0 - poisoning_score` | **Identified.** Should derive from injection detection, not poisoning score. Minor bug. |

---

## Final Computed Status

```
RESEARCH_STAGE = GATE_A_FORENSIC_TRUTH_AUDIT
ARCHITECTURE = CONCEPTUALLY_FROZEN
GATE_5 = FROZEN
COGNEE_POC = VERIFIED
COGNEE_FULL_BENCHMARK = NOT_EXECUTED
BASELINE_RETRIEVAL = OFFLINE_EXECUTED
TRUST = INTEGRATION_TESTED (MISSING_ZERO_ISSUE_DOCUMENTED)
SECURITY_COMPONENT = INTEGRATION_TESTED
SECURITY_E2E = NOT_EXECUTED

API_ADAPTERS = MOCK_TRANSPORT_TESTED (4 of 5)
LIVE_API_EXECUTION = NOT_EXECUTED

VERIFICATION_LAYER = INTEGRATION_TESTED (AnswerSafetyGate confirmed in orchestrator)
LLM_ADAPTER = MOCK_TRANSPORT_TESTED
REAL_PROVIDER_TRANSPORT = NOT_EXECUTED
MODEL_VERIFICATION = NOT_VERIFIED
STRUCTURED_OUTPUT = NOT_VERIFIED
CONFIGURATION_FREEZE = NO

TRACK_A_SCHEMA = FROZEN
TRACK_A_PROMPT = FROZEN
TRACK_A_DETERMINISTIC_TESTS = 28/28 PASS
TRACK_A_ANNOTATED = 31
TRACK_A_REMAINING = 499
TRACK_A_LABEL_FREEZE = NOT_FROZEN

MASTER_DATASET = UNTOUCHED
HUMAN_ANNOTATIONS = UNTOUCHED
P11_P60 = RESERVED
RETRIEVAL_BENCHMARK = LOCKED

CURRENT_BLOCKER = NO_API_CREDENTIALS
NEXT_GATE = GATE_C_LIVE_PROVIDER_VERIFICATION
```
