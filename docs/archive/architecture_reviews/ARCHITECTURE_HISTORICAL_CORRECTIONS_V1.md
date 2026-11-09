# ARCHITECTURE_HISTORICAL_CORRECTIONS_V1

| Old statement | Evidence | Correct interpretation | Current wording |
|---|---|---|---|
| BaseAdapterMock is the production baseline | pilot_adapter.py exists with real 
equests.post | Mock was for early tests; real adapter uses deterministic HTTP seams but no live APIs yet | "Provider-neutral adapter implemented with deterministic HTTP test seams; live execution pending." |
| Precomputed Cognee cache acts as live retrieval | Cognee POC files show real dd/cognify/search on test cases | Cache was a test fixture; actual Cognee local POC executes graph extraction | "Cognee local runtime POC (AIOSQLite/LanceDB) verified for test inputs." |
| Empty Cognee result means retrieval failure | cognee_adapter.py and POC scripts | Empty result can mean correctly pruned or no entities extracted; it is an expected state | "Cognee may legitimately return no candidates for specific queries." |
| Neo4j / Qdrant are the current backend | Environment configurations & POC scripts | They are conceptual/planned production backends; actual POC uses AIOSQLite/LanceDB | "Current verified POC uses AIOSQLite+LanceDB; Neo4j/Qdrant remain conceptual." |
| SimpleEmbeddingModel is the biomedical baseline | live_variants.py | It was a 7-word toy model; project authorized S-PubMedBert-MS-MARCO | "Biomedical dense retrieval baseline authorized as S-PubMedBert." |
| Synthetic security results prove E2E security | Unit tests for injection/poisoning | Detectors pass unit/component bounds but no live LLM E2E loop is executed | "Security detectors pass component-level deterministic tests; generative E2E remains unverified." |
| Prompt injection tests prove generative E2E | injection_detector.py tests | Pre-LLM gating works, but generative impact of bypassing is untested | "Prompt injection detector successfully blocks synthetic payloads at the pre-LLM gate." |
| Provider capabilities are live verified | gen_final_v14.py | Schema and parameters verified deterministically via mock, not live | "Provider compatibility is code-supported and documented, but not live-verified." |
| Static audit proves execution validation | Previous artifact generation | Static checks only prove structural presence | "Validation separated into STATIC_VERIFICATION, DETERMINISTIC_REAL_ADAPTER, and REAL_PROVIDER." |
