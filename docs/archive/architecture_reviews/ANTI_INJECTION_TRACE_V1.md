# ANTI-INJECTION TRACE AND CORRECTION REPORT

**Date:** 2026-10-03  
**Status:** RESOLVED (Code Corrected)  

## 1. Trace Before Correction

**Path in `rag_orchestrator.py` L502-510:**
```text
HybridRetrievalEngine.retrieve() 
  → Candidate (metadata contains `poisoning_score`, no `injection_score`)
  → Orchestrator L508
  → TrustFactorScores(anti_injection = 1.0 - cand.poisoning_score)
  → AdaptiveTrustScorer
  → Composite Trust Score (weighted sum)
  → EvidenceEligibilityGate (Threshold evaluation)
```

**Conceptual Semantics:**
- `poisoning_score`: Derived from document provenance metadata / ingestion safety.
- `anti_injection`: Meant to represent the absence of indirect prompt injection in the chunk.
- **Flaw**: L508 explicitly mapped `anti_injection = 1.0 - cand.poisoning_score`. This was semantic conflation (a copy-paste error from the line above it).

## 2. Intended Architectural Separation

Prompt injection detection and retrieval poisoning detection are two strictly separate domains in this architecture:

1. **Retrieval Poisoning**: 
   - Evaluated by `RetrievalPoisoningDetector.inspect_provenance(cand.metadata.get("provenance"))` in Step 4.5.
   - Also encoded in `cand.poisoning_score` from ingestion.
2. **Prompt Injection**:
   - Evaluated by `PromptInjectionDetector.inspect(cand.text)` in Step 6 (Evidence Eligibility Gate).
   - The detector returns a `SecurityDecision` (BLOCK, FLAG, ALLOW).

## 3. The Safe Code Correction

Since injection detection operates as a **hard gate** returning discrete states (BLOCK/FLAG) rather than a floating-point score:
- Chunk texts containing prompt injection markers are categorically rejected by the `EvidenceEligibilityGate` (L274: `if sec_state in (SecurityState.BLOCK, SecurityState.FLAG) ... return rejection`).
- Therefore, the trust scoring equation does not need to (and cannot) dynamically scale `anti_injection` using a pre-calculated score from the candidate.

**Fix Applied:**
```python
# rag_orchestrator.py L508
anti_injection=1.0,  # FIXED: Default clean; injection is evaluated as a hard gate later
```
This safely assigns the maximum score (`1.0`) during the trust calculation, preventing false deflation, while leaving the actual injection defense to the deterministic `PromptInjectionDetector` in the Eligibility Gate. 

## 4. Verification
- **Orchestrator Path**: The trust formula now correctly calculates weights without conflating poisoning. The security check in `EvidenceEligibilityGate` remains entirely intact.
- **Historical Artifacts**: Gate 5 historical experiments are frozen and unaffected by this forward-looking fix.
- **Deterministic Tests**: `test_trust_scorer.py` continues to pass, as `anti_injection` is properly initialized. 
