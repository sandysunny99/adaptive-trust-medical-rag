# Phase 14 Integration Map

This table maps the integration points based on the actual repository architecture.

| Stage | Existing Component | Integration Point | Input | Output | Security Decision |
|-------|--------------------|-------------------|-------|--------|-------------------|
| API Edge / Query Start | src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py | Top of process_query method, directly after sanitize | sanitized_query (str) | SecurityDecision | Allow / Block (Drop request entirely) |
| Retrieval / Candidate Loading | src/adaptive_trust_medical_rag/retrieval/hybrid_retrieval.py | After candidates are fetched but before returning them | list[ScoredCandidate] | dict[str, SecurityDecision] | Identify poisoned/tampered chunks |
| Evidence Eligibility | src/adaptive_trust_medical_rag/research_harness/gate_engine.py (EvidenceEligibilityGate) | Inside evaluate method | list[ScoredCandidate], 	rust_scores, poisoning_decisions | EligibilityResult | Exclude tampered chunks |
| Tool/Action Request | src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py | (Implicit in LLM parsing, needs explicit extraction) Before execution | ActionType, EntityDomain | SecurityDecision | ALLOW / UNAUTHORIZED_ACTION_REJECTED |
| Audit Logging | src/adaptive_trust_medical_rag/api/routes/audit.py (and session_memory.py) | Across all boundary checks | SecurityDecision | None (Appends to trace) | Persist decisions for transparency |

