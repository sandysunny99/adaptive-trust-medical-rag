# GATE B HUMAN DECISION PACKET

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)  
**Status:** 🔒 BLOCKED ON HUMAN RESEARCH DECISION

## 1. Current State of the Architecture

The architecture has been fully reconciled against the codebase line-by-line. All false claims (such as "Live Generative E2E" testing without a live LLM, or "Live Medical Source Querying" when relying on a frozen corpus) have been corrected to reflect actual evidence (`INTEGRATION_TESTED` / `OFFLINE_EXECUTED`).

- **Dynamic Integrity Validator:** Remains optional and unwired to preserve Gate 5 baseline.
- **Relationship Grounding (RG-02):** Remains optional and unwired to preserve Gate 5 recall metrics.
- **Anti-Injection Scoring:** The semantic conflation bug (L508) has been patched to `1.0`. Injection operates as a downstream boolean hard-gate.

## 2. The Unresolved Decision

Gate B is blocked on one critical research decision: the **Trust Missing-Value Policy**.

In the `AdaptiveTrustScorer`, two factors (`query_relevance` and `evidence_quality`) are never populated by the orchestrator, defaulting to `0.0`. This inflicts an automatic 30-35% penalty on all chunks, rendering the R3 Risk Tier (threshold 0.75) mathematically impassable.

## 3. The Three Options

Please explicitly authorize one of the following paths:

### Option A: Impute from Existing Signals
- **Action:** Derive `query_relevance` from the retrieval engine (e.g., RRF or Cosine Similarity). Derive `evidence_quality` from metadata defaults.
- **Risk:** Deriving trust from the retrieval score creates circularity. It makes the independent Trust Layer dependent on the retrieval engine, confounding comparisons between the Baseline and Cognee if their score distributions differ.

### Option B: Exclude and Renormalize
- **Action:** Remove the two missing factors from the formula and scale up the remaining 7 weights proportionally to sum to 1.0.
- **Risk:** Alters the fundamental 9-factor blueprint into a 7-factor model. Breaks Gate 5 historical comparability.

### Option C: Keep MISSING = ZERO
- **Action:** Accept the 0.0 defaults as a deliberate, fail-closed property of the current pipeline.
- **Risk:** Sacrifices the R3 risk tier (becomes impassable). However, exactly preserves Gate 5 historical reproducibility and avoids circularity.

## Next Steps

Once you select Option A, B, or C, Gate B will be closed, and the system will proceed to **Gate C: Live Provider Verification** (which requires provisioning a real LLM credential).
