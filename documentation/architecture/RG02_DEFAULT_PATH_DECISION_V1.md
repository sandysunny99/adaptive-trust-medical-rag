# RELATIONSHIP GROUNDING V2 (RG-02) PATH DECISION

**Date:** 2026-10-03  
**Status:** OPTIONAL EXPERIMENT (Not Default-Wired)

## 1. Trace and Evaluation

**Component:** `RelationshipGroundingValidatorV2` (in `src/adaptive_trust_medical_rag/security_extensions/relationship_grounding_v2.py`)
- **Detection Mechanism:** Extracts entities and relationships using NLP heuristics. Validates relationship polarity (positive, negated, ambiguous) against the source text to prevent bounded-negative hallucination (e.g., confusing "Drug A does not interact with Drug B" with "Drug A interacts with Drug B").
- **Default Value:** `None` in `AdaptiveTrustRAGOrchestrator` constructor (L375).
- **Orchestrator Use:** If injected, called in `EvidenceEligibilityGate` (L530-537). Statuses like `CONTRADICTED`, `NO_RELEVANT_RELATION`, or `ENTITY_PAIR_MISMATCH` trigger hard rejection.
- **Test Coverage:** High. Thoroughly unit-tested in `test_relationship_grounding_v2.py` and `test_relationship_polarity_v1.py`. 

## 2. Decision Logic

RG-02 is a highly sophisticated guardrail designed specifically for pharmacological relationships (DDI/ADE). 

**Is it a required core research guardrail?**
The core research architecture explicitly encompasses "verification, and controlled abstention", and the thesis statement focuses on "validating, qualifying, securing, verifying". 

However, examining the historical execution:
1. **Gate 5 Baseline:** The historical Gate 5 runs executed without RG-02 injected into the orchestrator.
2. **Current Limitations:** RG-02 relies on regex/NLP heuristics which are inherently brittle. Hard-wiring it by default into the `EvidenceEligibilityGate` with a fail-closed policy (rejecting on `NO_RELEVANT_RELATION`) would likely cause massive false-positive rejections across the benchmark, severely altering retrieval recall.
3. **Architectural Intent:** Relationship validation is largely handled by the *post-generation* `AnswerSafetyGate` (Stage 4 Contradiction Detection). RG-02 represents a *pre-generation* relationship filter.

## 3. Decision

**DECISION: KEEP OPTIONAL AND UNWIRED BY DEFAULT**

Enabling RG-02 by default would fundamentally alter the baseline retrieval metrics and invalidate comparisons against the frozen Gate 5 data. 

RG-02 remains **`UNIT_TESTED`** and **optional**. 
- It is available for specific ablation studies (e.g., "Impact of Pre-Generation Relationship Filtering").
- The main experimental pipeline will not claim pre-generation relationship filtering as a default active defense.
- Relationship contradiction detection will continue to be enforced safely *post-generation* via the `AnswerSafetyGate`.
