# Baseline Semantic Model Decision Matrix

## Current State: `BASELINE_AUTHORIZATION_AMBIGUOUS`

The audit found two parallel implementations:
1. `SimpleEmbeddingModel` (7-dim test fixture, used in orchestrator path)
2. `pritamdeka/S-PubMedBert-MS-MARCO` (768-dim real model, used in fusion experiment scripts)

Before Full Gate 5 can proceed, the research lead must explicitly choose one of the following options:

---

## OPTION A: Authorize S-PubMedBert-MS-MARCO
*Adopt the historical biomedical embedding model as the official Gate 5 dense baseline.*

*   **Requirements:**
    *   Explicit protocol amendment/decision record.
    *   Freeze exact HuggingFace revision hash.
    *   Define preprocessing specification (e.g., tokenization limits, max_length).
    *   Document offline provisioning method for air-gapped evaluation.
    *   Issue comparability statement invalidating prior `SimpleEmbeddingModel` runs.
*   **Pros:** It is a real semantic model, matches the architecture `VECTOR(768)` spec, was historically used in `fusion-evaluation-v3`, and provides meaningful dense retrieval for Gate 5.
*   **Cons:** Breaks comparability with any prior test run that relied on the orchestrator's default path (including early `FREE_REPLICATION` tests).

## OPTION B: Keep SimpleEmbeddingModel
*Authorize the deterministic test fixture as the frozen baseline constraint.*

*   **Requirements:**
    *   Explicit protocol authorization stating the semantic channel is deliberately constrained.
    *   Document the limitation that key queries (like POS-01) will have 0% dense retrieval recall.
*   **Pros:** Preserves strict determinism. Requires no new dependencies or cache downloads.
*   **Cons:** Renders the dense retrieval evaluation mathematically meaningless for most real-world queries. Contradicts the `VECTOR(768)` database spec.

## OPTION C: Define Another Semantic Model
*Choose a different model (e.g., `BAAI/bge-large-en-v1.5`, `all-MiniLM-L6-v2`).*

*   **Requirements:**
    *   Explicit protocol decision and rationale for rejecting the historical `S-PubMedBert`.
    *   Version freeze and offline provisioning plan.
    *   Full comparability analysis.
*   **Pros:** May offer better general performance or smaller footprint.
*   **Cons:** Introduces a brand-new independent variable that has zero historical project usage, requiring a complete protocol rewrite.

## OPTION D: Leave Baseline Undefined
*Do not make a decision.*

*   **Consequence:** Full Gate 5 remains **BLOCKED**.

---

## Recommendation based on Historical Evidence

**Option A** is the only scientifically defensible path that aligns with the historical experimental intent. `S-PubMedBert` was the intended baseline for semantic evaluation in Phase 14 (`fusion-evaluation-v3`), and its absence from the orchestrator path was simply an integration oversight.

`evidence_source`: `manual_analysis`
