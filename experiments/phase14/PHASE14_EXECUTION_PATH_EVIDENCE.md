# Phase 14 Security Execution Path Evidence

## 1. Prompt Injection Defense
**File:** src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py
**Function:** AdaptiveTrustRAGOrchestrator.query(self, request: RAGRequest)
**Actual Call Path:**
The PromptInjectionDetector evaluates the raw equest.query precisely at step 1.5, before any normalization or retrieval logic occurs. If the detector issues a SecurityState.BLOCK, the query is halted, and _abstain is returned.
**Test Proof:** 	est_prompt_injection_blocked in 	ests/security/test_phase14_integration.py utilizes mocks for the retriever and LLM engine to assert call_count == 0, demonstrating that a blocked request never initiates retrieval or generation.

## 2. Retrieval Poisoning Defense
**File:** src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py
**Function:** AdaptiveTrustRAGOrchestrator.query(self, request: RAGRequest)
**Actual Call Path:**
Post hybrid-retrieval (step 4), the RetrievalPoisoningDetector is invoked in a loop across all candidate evidence chunks (step 4.5). The resulting decisions (SecurityDecision) are appended to a dictionary etrieval_security_states.
At step 6, self._eligibility_gate.evaluate(...) ingests this dictionary. Inside EvidenceEligibilityGate, chunks whose associated security state is BLOCK are immediately appended to ejected_ids and dropped from the contextual evidence array before LLM generation.
**Test Proof:** 	est_retrieval_poisoning_excluded asserts that the retrieved chunk IDs array in the final RAGResponse successfully omits poisoned sources while retaining benign ones.

## 3. Authorization Boundary Defense
**File:** src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py
**Function:** AdaptiveTrustRAGOrchestrator.query(self, request: RAGRequest)
**Actual Call Path:**
Post-eligibility evaluation (step 6.5), the orchestrator triggers AuthorizationBoundary.authorize(). It explicitly evaluates security_context.principal (the actor calling the system) against EntityDomain(security_context.principal). Any violation throws a UNAUTHORIZED_ACTION_REJECTED state, returning an immediate abstention. 
**Test Proof:** 	est_authorization_execution_boundary mocks the authorization gate to issue a failure and explicitly spies on orchestrator._llm.generate to prove call_count == 0 if authorization fails, guaranteeing the privileged action is skipped.

