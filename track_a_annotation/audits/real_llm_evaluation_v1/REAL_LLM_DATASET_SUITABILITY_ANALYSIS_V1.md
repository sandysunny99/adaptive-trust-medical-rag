# REAL-LLM V1.1 FINAL DATASET SUITABILITY ANALYSIS

## 1. Dataset Structural Analysis
**File**: experiments/manifests/v3_1_human_cases.json
The dataset is highly minimal. Each case contains:
- case_id (string): Unique identifier
- query (string): Medical question
- claim_type (string): Categorization of claim
- isk_tier (string): Designated risk tier (e.g., R1)
- difficulty (string): Difficulty classification
- expected_entities (list of strings): Target entities
- nnotation_status (string): Current annotation state

**Ground Truth Fields**:
- medical_reference_answer: NOT FOUND
- eference_explanation: NOT FOUND
- eference_DDI_decision: NOT FOUND
- eference_ADE_decision: NOT FOUND
- clinical_correctness_label: NOT FOUND
- expected_response: NOT FOUND
- expected_abstention_label: NOT FOUND

**Conclusion**: ANSWER_LEVEL_MEDICAL_GROUND_TRUTH = NOT_AVAILABLE.

## 2. Original Purpose
- **Original Intended Use**: Retrieval and Evidence Evaluation.
- **Support for V1.1 (Evidence-Grounding Generation)**: PARTIALLY_SUPPORTED. The queries and historical retrievals allow testing of evidence-grounding (via claim_support_rate) and abstention triggering, but CANNOT establish clinical correctness.

## 3. Metric Feasibility Analysis
| Metric | Data required | Dataset provides it? | Implementation provides it? | Status | Limitation |
|---|---|---|---|---|---|
| claim_support_rate | Queries, frozen evidence, Common Evaluator | YES (queries) | YES (evaluator & retrieval history) | FULLY_SUPPORTED | Measures evidence grounding, NOT clinical correctness. |
| citation_validation_rate | Citations, frozen evidence | YES | YES | FULLY_SUPPORTED | Validates mapping only. |
| unsupported_answer_rate | Generated claims, evidence | YES | YES | FULLY_SUPPORTED | Relies on automated verification. |
| abstention_rate | Observed system output | YES | YES | FULLY_SUPPORTED | OBSERVED ONLY. Abstention correctness cannot be evaluated. |
| provider_failure_rate | Execution logs | YES | YES (Harness enforces retry=0) | FULLY_SUPPORTED | Must use isolated harness. |

## 4. Track A Contamination Analysis
- **Contamination Risk**: LOW.
- **Reason**: V1.1 is defined as a READ-ONLY consumer of historical retrieval evidence and the 80 test cases. Track A annotations, benchmarks, and historical metrics remain strictly isolated and unchanged.

## 5. Methodological Suitability
**YES, WITH LIMITATIONS**. The dataset can support V1.1 provided that the evaluation explicitly bounds its claims to *evidence grounding* (not medical accuracy), reports abstention as *observed* (not correct/incorrect), and uses the isolated harness to prevent provider metric contamination.

## 6. Provider Policy Check
**GAP**: The default implementation (src/adaptive_trust_medical_rag/llm_routing/config.py) defaults to etry_max_attempts = 3 and enables failover. The V1.1 protocol requires etry = 0 and ailover = disabled. 
**Resolution**: The isolated ExperimentRunner harness built in the previous V1.2 dry run explicitly suppresses retries and failovers, which MUST be used to execute the evaluation.

## 7. Protected State
- **Status**: PASS (All artifacts unchanged).
