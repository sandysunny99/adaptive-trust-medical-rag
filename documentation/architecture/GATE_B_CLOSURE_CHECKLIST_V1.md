# GATE B CLOSURE CHECKLIST

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)  

This checklist defines the exact actions required to close Gate B and transition to Gate C.

## 1. MUST DECIDE BY HUMAN
- [ ] **Trust Missing-Value Policy:** Select Option A, B, or C to resolve the `query_relevance` and `evidence_quality` 0.0 defaults.
- [ ] **Anti-Injection Representation:** Select whether to keep structural constant 1.0, exclude it, or redefine it as a continuous signal.

## 2. MUST FIX IN CODE
- [ ] Implement the authorized changes for the Trust Missing-Value Policy (only if Option A or Option B is selected).
- [ ] Implement the authorized changes for Anti-Injection (only if Option B or Option C is selected).

## 3. MUST UPDATE DOCUMENTATION
- [ ] Update `trust.yaml` weights (if Option B is selected).
- [ ] Update `CANONICAL_MEDICAL_RAG_ARCHITECTURE_V1.md` if the Trust Policy changes from a 9-factor model.
- [ ] Generate `ARCHITECTURE_FREEZE_CERTIFICATE_V1.md`.

## 4. MUST RERUN (If Methodology Changed)
- [ ] Rerun Gate 5 baseline experiments (ONLY IF Option A or Option B is selected for either open decision, as historical scores would become incomparable).

## 5. DO NOT TOUCH
- [ ] Historical Gate 5 artifacts (unless explicitly authorized to overwrite them via a rerun decision).
- [ ] Track A frozen schema and prompts.
- [ ] Completed human annotations (Track A).
- [ ] Frozen corpus 2.0.0.

## 6. ALREADY RESOLVED
- [x] Security Status Contradictions (Corrected to `INTEGRATION_TESTED` / `OFFLINE_EXECUTED`).
- [x] API Classifications (Corrected to `MOCK_TRANSPORT_TESTED`).
- [x] Dynamic Integrity Validator (Confirmed as `OPTIONAL EXPERIMENTAL COMPONENT`).
- [x] Relationship Grounding V2 (Confirmed as `OPTIONAL EXPERIMENTAL COMPONENT`).

## 7. BLOCKED UNTIL GATE C
- [ ] Live LLM Provider Verification.
- [ ] Real LLM API Execution.
- [ ] Generative E2E Security Validation.
