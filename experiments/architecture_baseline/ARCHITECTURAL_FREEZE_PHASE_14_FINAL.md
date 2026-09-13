# ARCHITECTURAL FREEZE (Phase 14 Final Checkpoint)

## 1. Security Plane

**CANONICAL SECURITY PLANE = CUSTOM SECURITY CORE**
- `PromptInjectionDetector`
- `RetrievalPoisoningDetector`
- `AdaptiveTrustScorer`
- `EvidenceEligibilityGate`
- `AnswerSafetyGate`
- `AuthorizationBoundary`

**Rationale:** The Custom Core is the provisional architectural choice for Phase 15. It was empirically executable in the locked environment and preserves the medical authorization/security boundary natively.

**EXTERNAL FRAMEWORKS = OPTIONAL / NOT SCIENTIFICALLY BENCHMARKED**
- `nemoguardrails`
- `guardrails-ai`

**Scientific Wording Safeguard:** The Custom Core is the provisional architectural choice, not a scientifically proven superior guardrail framework. The observed failures for external frameworks establish environment-specific reproducibility/integration constraints under the tested configuration; they do not establish intrinsic security deficiencies of those frameworks.

## 2. Provider / Router Plane

The Provider/Router Plane is **strictly separated** from the Security Plane.
- **Resilient Routing:** Supports bounded retries and failover to secondary providers (e.g., Gemini → Groq) on transient availability errors (429, 503, timeouts).
- **Isolation:** Security rejections (`BLOCK`, `FLAG`, `SCHEMA_REJECTED`, `UNAUTHORIZED_ACTION_REJECTED`) do *not* trigger provider failover.
- **Scientific Mode:** In Phase 15, failover is disabled to guarantee provider/model attribution remains pure.

## 3. Invariants Preserved for Phase 15

- **Phase 15 Hash:** `af71c70d36081b1b68316b5ff8636969c8b964c9655f752b41112694ebc02c48`
- **Phase 15 Observations:** 0
- **Phase 15 Evaluation API Calls:** 0
- **Regression Suite:** 806 tests passing (Engineering checkpoint, not a security effectiveness proof).

This architecture is now considered **STABLE** and frozen for the upcoming Phase 15 confirmatory experiment.
