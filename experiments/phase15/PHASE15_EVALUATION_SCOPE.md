# Phase 15 Evaluation Scope

## 1. Classification of Evaluation Level

The Phase 15 scientific evaluation is strictly classified as an **ORCHESTRATOR-LEVEL END-TO-END EVALUATION**.

This terminology explicitly disclaims "production", "clinical", or "full-system" validation. The scope is bounded to the execution graph of the `AdaptiveTrustRAGOrchestrator` instance.

## 2. Executable-Path Checklist

The Phase 15 runner actually exercises the following path. Every stage is explicitly mapped to its invocation point:

| Stage | Invocation Point in Code | Verification Evidence |
|-------|--------------------------|-----------------------|
| **API/Query Acceptance** | `rag_orchestrator.py: AdaptiveTrustRAGOrchestrator.query(request)` | Call initialization |
| **Query Security** | `injection_detector.py: PromptInjectionDetector.inspect()` | Orchestrator step 1.5 |
| **Pharmacology/Entity Handling** | `drug_normalizer.py: _normalize_drugs()` | Orchestrator step 2 |
| **Retrieval** | `hybrid_retrieval.py: HybridRetrievalEngine.retrieve()` | Orchestrator step 4 |
| **Evidence Processing** | `poisoning_detector.py: inspect_provenance()` | Orchestrator step 4.5 |
| **Security Gate 1 (Trust)** | `trust_scorer.py: AdaptiveTrustScorer.score()`, `EvidenceEligibilityGate` | Orchestrator steps 5, 6 |
| **Generation** | `llm_backend.py: generate()` | Orchestrator step 7 |
| **Final Verification (Gate 2)** | `claim_verifier.py: AnswerSafetyGate.verify()` | Orchestrator step 8 |
| **Final Response Classification** | `rag_orchestrator.py: return RAGResponse` | Return object formatting |
| **Audit/Trace Capture** | `rag_orchestrator.py: _log()` to `audit` array | `RAGResponse.audit_log` |

## 3. Excluded Layers

The following production layers are intentionally excluded and mocked/bypassed during this evaluation:
- External network ingress / WAF.
- Authentication/SSO middleware.
- Production UI/Frontend rendering.
- Database scaling/sharding latency.
