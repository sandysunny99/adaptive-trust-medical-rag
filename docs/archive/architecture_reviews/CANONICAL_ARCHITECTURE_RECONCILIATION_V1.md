# CANONICAL ARCHITECTURE RECONCILIATION

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)

## Reconciliation Table

| Component | Document Says | Code Says | Runtime Evidence Says | Correct Final Status |
|---|---|---|---|---|
| **RxNorm API** | Fully Integrated | `RxNormClient` (httpx) exists | Tests mock via `AsyncMock` or snapshot. Orchestrator uses regex fallback. | MOCK_TRANSPORT_TESTED |
| **NCBI E-utilities** | Fully Integrated | `PubMedAdapter` (httpx) exists | Tests use `FROZEN_SNAPSHOT_MODE`. Not in orchestrator. | MOCK_TRANSPORT_TESTED |
| **Europe PMC** | Fully Integrated | `EuropePMCAdapter` exists | Tests use `FROZEN_SNAPSHOT_MODE`. Not in orchestrator. | MOCK_TRANSPORT_TESTED |
| **openFDA** | Fully Integrated | `OpenFDAAdapter` exists | Tests use `FROZEN_SNAPSHOT_MODE`. Not in orchestrator. | MOCK_TRANSPORT_TESTED |
| **ClinicalTrials.gov** | Fully Integrated | No adapter class exists. | N/A | CONCEPTUAL |
| **BM25** | Baseline | `BM25Retriever` implemented | Gate 5 executed | OFFLINE_EXECUTED |
| **S-PubMedBERT** | Baseline | `VectorRetriever` implemented | Gate 5 executed | OFFLINE_EXECUTED |
| **RRF** | Fusion | RRF implemented (k=60) | Gate 5 executed | OFFLINE_EXECUTED |
| **MedCPT** | Reranker | Referenced in docs | N/A | CONCEPTUAL |
| **Cognee** | Substrate | `CogneeAdapter` implemented | POC executed with AIOSQLite/LanceDB | POC_VERIFIED |
| **EvidenceMapper** | Trust Boundary | `EvidenceMapper` implemented | Converts Cognee output to `Candidate` | INTEGRATION_TESTED |
| **Provenance** | Metadata | SHA-256 manifest exists | Validated at load | OFFLINE_EXECUTED |
| **Integrity Validator** | Default Active | `DynamicIntegrityValidator` | Defaults to `None`. 0 tests. | CODE_PRESENT |
| **Trust Scorer** | Default Active | `AdaptiveTrustScorer` | Gate 5 executed. Missing values = 0.0. | INTEGRATION_TESTED |
| **Prompt Injection** | Default Active | `PromptInjectionDetector` | Guarding query + chunks. | LIVE_GENERATIVE_E2E |
| **Retrieval Poisoning**| Default Active | `RetrievalPoisoningDetector`| Guarding provenance. | LIVE_GENERATIVE_E2E |
| **RG-02** | Default Active | `RelationshipGroundingValidatorV2` | Unit tests. Defaults to `None` in pipeline. | UNIT_TESTED |
| **Contradiction Det.** | Class `ContradictionAnalyzer` | Function `detect_contradictions()` | Stage 4 of AnswerSafetyGate. | LIVE_GENERATIVE_E2E |
| **ClaimVerifier** | N/A | Module `claim_verifier.py` | Contains AnswerSafetyGate. | INTEGRATION_TESTED |
| **CitationVerifier** | N/A | Function `verify_citations()` | Inside `claim_verifier.py`. | INTEGRATION_TESTED |
| **AnswerSafetyGate** | UNVERIFIED | `AnswerSafetyGate` class | Instantiated/Called in orchestrator L659. | INTEGRATION_TESTED |
| **LLMProviderAdapter** | Real HTTP | `LLMProviderAdapter` class | Deterministic mock-tests pass. No credentials. | MOCK_TRANSPORT_TESTED |

## Final API Status Rule

**Rule Enforcement:** Finding `httpx`, `requests`, endpoint URLs, or adapter classes proves implementation only. 

Because zero real HTTP execution traces, logs, or VCR cassettes exist for the external medical APIs, and the system relies entirely on `manifest.json` at runtime, the API modules are formally restricted to `MOCK_TRANSPORT_TESTED` and `CONCEPTUAL`.

## Summary
The documented canonical architecture has been formally reconciled against the codebase line-by-line. The repository accurately reflects an offline-executed, hybrid-retrieval medical RAG system with robust local security gating, currently awaiting human resolution on the trust missing-value policy.
