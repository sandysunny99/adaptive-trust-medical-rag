# Phase 14 Architecture to Code Conformance

This document maps the Phase 14 security architecture components to their specific physical implementation in the codebase, providing execution-path evidence of their integration.

## 1. Prompt Injection Defense
- **Architecture Role:** Step 1.5, pre-sanitization inspection of the raw user query. Fail-closed.
- **Implementation:** `src/adaptive_trust_medical_rag/security_extensions/injection_detector.py`
- **Integration Point:** `rag_orchestrator.py` inside `query()` (Step 1.5).
- **Execution Evidence:** `test_pi01_direct_instruction_override` proves that a `BLOCK` decision halts execution with `retrieval.call_count == 0` and `llm.call_count == 0`.

## 2. Retrieval Poisoning Exclusion
- **Architecture Role:** Step 4.5, post-retrieval candidate inspection based on provenance. Fail-safe (drop poisoned chunk, retain clean chunks).
- **Implementation:** `src/adaptive_trust_medical_rag/security_extensions/poisoning_detector.py`
- **Integration Point:** `rag_orchestrator.py` inside `query()` (Step 4.5).
- **Execution Evidence:** `test_retrieval_poisoning_excluded` proves that `c2` (poisoned) is excluded from `retrieved_chunk_ids` while `c1` (clean) is retained and sent to the LLM context.

## 3. Pre-Generation Evidence Eligibility Gate (Gate 1)
- **Architecture Role:** Step 6, evaluate candidate trust, poisoning scores, and security states before LLM context construction.
- **Implementation:** `src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py` (`EvidenceEligibilityGate` class).
- **Integration Point:** `rag_orchestrator.py` inside `query()` (Step 6).
- **Execution Evidence:** `test_poisoned_chunk_rejected` and `test_low_trust_chunk_rejected` in `test_rag_orchestrator.py` prove chunks are dropped and trigger abstention if minimums are not met.

## 4. Fail-Closed Action Parsing
- **Architecture Role:** Step 7.5, strictly typed extraction of `[ACTION: X ON Y]` markers.
- **Implementation:** `src/adaptive_trust_medical_rag/security/agent_action.py`
- **Integration Point:** `rag_orchestrator.py` inside `query()` (Step 7.5).
- **Execution Evidence:** `test_malformed_action_no_parse` and `test_unknown_action_type_raises` prove that invalid actions raise `ActionParseError` and trigger controlled abstention instead of falling back to unsafe defaults.

## 5. Authorization Boundary
- **Architecture Role:** Step 7.5, verify if Principal is allowed to execute ActionType on EntityDomain.
- **Implementation:** `src/adaptive_trust_medical_rag/security_extensions/boundary_enforcer.py`
- **Integration Point:** `rag_orchestrator.py` inside `query()` (Step 7.5).
- **Execution Evidence:** `test_unauthorized_action_no_tool_execution` proves that a `USER` requesting `MODIFY_TRUST_CONFIG` on `SYSTEM` results in `execution_count == 0`.

## 6. Post-Generation Answer Safety Gate (Gate 2)
- **Architecture Role:** Step 8, extract atomic claims, align to cited evidence, check contradictions.
- **Implementation:** `src/adaptive_trust_medical_rag/verification/claim_verifier.py`
- **Integration Point:** `rag_orchestrator.py` inside `query()` (Step 8).
- **Execution Evidence:** `test_unsafe_answer_triggers_abstention` proves that LLM-generated absolute/unsafe language triggers Gate 2 abstention and overrides a release.
