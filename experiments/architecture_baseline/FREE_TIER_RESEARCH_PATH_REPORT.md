# Free-Tier Research Path Report

> [!IMPORTANT]
> The canonical Phase 15 experiment is currently BLOCKED due to a zero-quota Free-Tier restriction on the exact frozen model. It is NOT failed, and it will NOT be modified. This report outlines a separate, free-tier-compatible replication pathway and the independent continuation of Track A.

## 1. Current Scientific State

```text
ENGINEERING_STATUS              = CLOSED
SCIENTIFIC_VALIDATION_STATUS    = IN_PROGRESS
TRACK_A_STATUS                  = PENDING
PHASE15_STATUS                  = FROZEN / NOT_STARTED
PHASE15_PREFLIGHT_STATUS        = BLOCKED
PHASE15_BLOCK_REASON            = GEMINI_FREE_TIER_UNAVAILABLE
PHASE15_PROVIDER                = gemini
PHASE15_MODEL                   = gemini-3.1-pro-preview
PHASE15_FAILOVER                = DISABLED
PHASE15_PROVIDER_IMMUTABLE      = TRUE
PHASE15_EXECUTION_STARTED       = NO
PHASE15_API_CALLS               = 0
PHASE15_OBSERVATIONS            = 0
```

---

## 2. Why Canonical Gemini Pro Cannot Use Free API Tier

Current Google documentation explicitly states that `gemini-3.1-pro-preview` has **NO FREE TIER** for Gemini API usage. While it can be tested in Google AI Studio, programmatic API requests via the Free Tier result in a `429 RESOURCE_EXHAUSTED` error with a quota `limit: 0`. 

Because this is a strict provisioning boundary and not an ordinary daily usage limit, **waiting for a midnight reset will not restore access.** The blocker is `GEMINI_FREE_TIER_UNAVAILABLE`.

The canonical Phase 15 experiment remains frozen to this model and will be held in a blocked state without modification.

---

## 3. Track A Continuation Plan

Track A has no dependency on the Gemini LLM. It relies entirely on human annotation and the frozen Phase 13/14 retrieval outputs.

*   **Objective:** Complete the 530 remaining blinded annotations.
*   **Methodology:**
    *   Reviewer A and Reviewer B annotate independently.
    *   Calculate Inter-Annotator Agreement (Cohen's kappa).
    *   Execute consensus adjudication for disagreements.
    *   Finalize the 600-position benchmark dataset.
    *   Perform F0 vs F3 statistical retrieval analysis.
*   **Constraints:** The existing 70 labels are diagnostic only. No retrieval rank information (F0 vs F3) will be exposed to reviewers. The corpus and frozen outputs will not be regenerated.

---

## 4. Available Free Gemini Models

While the Pro Preview model is blocked, the Google Gemini API Free Tier provides non-zero quotas (subject to strict RPM/TPM limits) for several Flash-class models:

*   `gemini-3.5-flash`
*   `gemini-3.1-flash-lite`
*   `gemini-2.5-flash`
*   `gemini-2.5-flash-lite`

---

## 5. Model Capability Comparison

| Feature | Canonical (`gemini-3.1-pro-preview`) | Candidate (e.g., `gemini-3.5-flash`) |
| :--- | :--- | :--- |
| **Tier** | Pro (High-tier reasoning) | Flash (Speed/Efficiency tier) |
| **Context Window** | 1M tokens | 1M tokens |
| **Structured Output** | JSON Schema Supported | JSON Schema Supported |
| **Function Calling** | Supported | Supported |
| **Free API Quota** | **0 RPM / 0 RPD** | e.g., 15 RPM, 1M TPM, 1,500 RPD |

---

## 6. Scientific Comparability Analysis

*   **CAN_REPLICATE_EXPERIMENTAL_STRUCTURE = YES**
    Flash models support the required context lengths, JSON schemas, and function calling required to run the orchestrator-level benchmark.
*   **CAN_REPRODUCE_CANONICAL_MODEL_TREATMENT = NO**
    Flash models possess different parameter scales, training priors, safety behaviors, and reasoning depths compared to the Pro Preview model. Evaluating the security gates with a Flash model constitutes a fundamentally different experimental condition.

Therefore, a Free-tier model **cannot** serve as a substitute for Phase 15. It must be treated as a separate replication.

---

## 7. Proposed Free-Model Replication Design

**Name:** `PHASE15_FREE_MODEL_REPLICATION`

*   **New Protocol ID:** Required to document the shift to a Flash model.
*   **New Configuration ID:** Required for the updated generation settings/provider declarations.
*   **New Dataset Reference:** The frozen 200-case Phase 15 dataset MAY be reused as the input benchmark, strictly mapping inputs to the new replication path.
*   **New Manifest & Run ID:** Guaranteed isolation.
*   **New Statistical Analysis:** Computes baseline SFR, hardened SFR, exact McNemar test, and confidence intervals **exclusively** for the Flash model observations.

**Research Question:** *"Does the security architecture exhibit similar protection behavior when the same orchestrator-level evaluation is executed with a lower-tier/free-access language model?"*

---

## 8. Risks and Limitations

*   **Free-Tier Quota Exhaustion:** Flash models on the Free tier have strict RPM constraints (e.g., 15 RPM). The replication runner must include aggressive rate-limit handling and backoffs to prevent silent failure or dropped cases during the 400-call execution.
*   **Different Baseline Hallucination Rates:** Lower-tier models may exhibit higher baseline hallucination or compliance failures, which could skew the delta between Baseline and Hardened states differently than the Pro model.

---

## 9. Separate Experiment Naming/Versioning

*   The results of `PHASE15_FREE_MODEL_REPLICATION` must **never** be merged with the canonical Phase 15 results.
*   Observations cannot be pooled across models.
*   The Phase 15 canonical codebase must remain isolated from this alternative configuration.
*   Groq, Cloudflare, and Hugging Face remain firmly inside the operational routing plane and are NOT permitted as fallbacks for either scientific experiment.

---

## 10. Exact Next Action

1.  **Maintain Phase 15 Freeze:** Acknowledge `PHASE15_STATUS = BLOCKED` due to `GEMINI_FREE_TIER_UNAVAILABLE`.
2.  **Proceed with Track A:** Wait for explicit user authorization to initiate the blinded annotation workflow environment.
3.  **Prepare Free Replication (Optional):** Wait for explicit user authorization to instantiate the isolated codebase/configuration for `PHASE15_FREE_MODEL_REPLICATION`. No execution will occur yet.
