# COGNEE GATE 5 CORRECTION 05 CODE AUDIT

## 1. Actual Application Path
The core runtime integrates directly via AdaptiveTrustRAGOrchestrator.__init__ which natively accepts etrieval_engine=None. The fallback is HybridRetrievalEngine. For Cognee, CogneeRetrievalAdapter (located natively in src/adaptive_trust_medical_rag/retrieval/cognee_adapter.py) connects directly to cognee.search() and yields Candidate objects via EvidenceMapper.
**Status:** Native integration established. No lambda monkey-patches remain in production source.

## 2. Actual Experiment Path
In Correction 05, the test harness initializes the orchestrator explicitly:
- For COGNEE=ON: AdaptiveTrustRAGOrchestrator(retrieval_engine=CogneeRetrievalAdapter(...))
- For COGNEE=OFF: AdaptiveTrustRAGOrchestrator(retrieval_engine=HybridRetrievalEngine(canonical_baseline_corpus))
**Status:** Clean separation of true native retrieval vs baseline retrieval.

## 3. Test-Only Wrappers
To facilitate deterministic security testing (e.g., integrity mismatch, missing provenance), a TamperingRetrievalWrapper is employed *only* in the experiment script. It transparently wraps the CogneeRetrievalAdapter or HybridRetrievalEngine, mutating candidates *post-retrieval* before they enter the gating system.
**Status:** Valid for security simulation. Will be explicitly tagged as REAL_COGNEE_WITH_CONTROLLED_POST_RETRIEVAL_TAMPERING.

## 4. Mocks
- **RxNorm:** Remains mocked via MockNormalizer mapping terms deterministically to avoid unrelated vector noise.
- **LLM:** Remains mocked via MockLLM. Generation is isolated.
- **Embeddings (for OFF path):** MockEmbeddingModel used solely for the local test harness to preserve deterministic execution without requiring heavy local LLMs during gating checks. (Cognee paths use FastEmbed natively).

## 5. Dependency Injection Points
- etrieval_engine
- drug_normalizer
- grounding_validator
- integrity_validator
- llm_backend
**Status:** Safe and conforming to SOLID principles.

## 6. Baseline Fallback Path
The baseline path leverages HybridRetrievalEngine. In Correction 05, it will be strictly populated using the canonical COGNEE_GATE5_TRUSTED_SOURCE_MANIFEST_V2.jsonl rather than an ad-hoc constructed candidate.
