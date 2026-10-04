# DYNAMIC INTEGRITY VALIDATOR DECISION

**Date:** 2026-10-03  
**Status:** OPTIONAL EXTENSION (Not Default-Wired)

## 1. Trace and Evaluation

**Component:** `DynamicIntegrityValidator` (in `src/adaptive_trust_medical_rag/security_extensions/integrity_validator.py`)
- **Detection Mechanism:** Cryptographic SHA-256 content-hash verification against a `registry_store`.
- **Default Value:** `None` in `AdaptiveTrustRAGOrchestrator` constructor (L376).
- **Orchestrator Use:** If injected, it is called in the `EvidenceEligibilityGate` loop (L538-539). If `IntegrityDecision` is `MISMATCH` or `MISSING`, the chunk is blocked.
- **Test Coverage:** Zero unit tests. Zero integration tests in the test suite. 

## 2. Decision Logic

**Is it a required core architecture component?**
The core research architecture relies on the frozen evidence corpus (manifest.json) which inherently computes and validates SHA-256 hashes upon load (`live_variants.py`). Thus, basic static integrity is already enforced at corpus-load time.

`DynamicIntegrityValidator` enforces runtime, chunk-by-chunk cryptographic verification against an external registry. This is an advanced security defense against vector-database poisoning or transit tampering.

However, the frozen experimental benchmark (Gate 5) executed entirely without this validator injected. Enabling it by default now would:
1. Break backward compatibility with Gate 5 execution pathways.
2. Introduce a new, untested component into the critical path.
3. Fail immediately in standard queries because a `registry_store` is not constructed or passed by default.

## 3. Decision

**DECISION: KEEP OPTIONAL AND UNWIRED BY DEFAULT**

`DynamicIntegrityValidator` is classified as an **optional, advanced security extension**. It is not required for the core pharmacological hallucination reduction benchmark. 

It will remain as `CODE_PRESENT`. We will explicitly document its boundary: it is available for production deployment but is not part of the active research benchmark. It must not be enabled without first adding comprehensive unit tests and providing a valid `registry_store`.
