# REAL LLM EVALUATION PROTOCOL V1.3

## 1. Purpose
To obtain a sufficiently reliable and balanced real-LLM experimental execution so that Arm A and Arm B have comparable opportunity to reach the LLM generation stage and their system-level behavior can be evaluated.

## 2. Research Question
Does the adaptive trust-aware Medical RAG system behave differently from the baseline system with respect to evidence-grounded answer generation, citation support, unsupported-answer behavior, and controlled abstention?

## 3. Experimental Hypotheses
H1: Arm B produces fewer unsupported answers than Arm A under comparable generation conditions.
H2: Arm B exhibits a higher pre-generation abstention rate due to evidence eligibility gating.

## 4. Experimental Unit
N = 80 human-case IDs (160 paired requests).

## 5. Dataset
experiments/manifests/v3_1_human_cases.json (Hash: db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc)

## 6. Case/Arm Structure
80 paired cases. Each case executes Arm A and Arm B sequentially.

## 7. Arm A Definition
Baseline system. Semantic retrieval -> LLM generation -> No post-generation modification.

## 8. Arm B Definition
Adaptive system. Semantic retrieval + Adaptive Trust Scorer (Evidence Gate) -> LLM generation -> Claim Verifier V2 (Answer Gate).

## 9. Frozen Prompt
REAL_LLM_EVALUATION_PROMPT_V1_2.txt (Hash: e5aeb4fa105d30f9df23c6d3815a45d4d63c7e83b82ab30e5fbb9f4721e4301c)

## 10. Frozen Retrieval
FROZEN_HISTORICAL_OUTPUT

## 11. Provider and Model
Groq with openai/gpt-oss-120b.

## 12. Temperature / Sampling
Temperature: 0.

## 13. Retry Policy
Allowed ONLY for HTTP 429 and 50x transport errors.
Max retries: 3.
Delay: Exponential backoff (5s, 10s, 20s).
Not allowed for: safety failure, evidence eligibility, claim verification.

## 14. Rate-Limit Policy
Pacing: 5 seconds delay between requests to avoid TPM limits.

## 15. Failover Policy
None. Provider outage causes protocol-defined failure.

## 16. Request Pacing
Strictly sequential. 5 seconds gap between any request.

## 17. Concurrency
Sequential. Maximum concurrency = 1.

## 18. Authorization Gate
Requires environment flag `RESEARCH_EVAL_AUTHORIZED=1` and `V1_3_RUN_ID` defined.

## 19. Request Telemetry
Must log: request_id, run_id, case_id, arm, timestamp_start, timestamp_end, provider, model, temperature, prompt_hash, dataset_hash, case_id_hash, retrieval_identity, status, retry_count.

## 20. Status Taxonomy
- SUCCESS
- ABSTAINED
- PROVIDER_FAILURE
- APPLICATION_FAILURE

## 21. Evidence Eligibility
Defined by TrustScorer thresholds.

## 22. Controlled Abstention
Triggered by Evidence Gate (pre-generation) or Answer Gate (post-generation).

## 23. Claim Verification
V2 Semantic Judgments + Canonical Identity match.

## 24. Metrics
- successful_generation_rate (SUCCESS / total requests)
- provider_failure_rate (PROVIDER_FAILURE / total requests)
- abstention_rate (ABSTAINED / total requests)
- unsupported_answer_rate (Answers with unsupported claims / GENERATED answers)
- claim_support_rate (Supported claims / total claims in GENERATED answers)
- citation_validation_rate (Valid citations / total citations in GENERATED answers)

## 25. Denominators
Execution metrics use N=80 (requests per arm). Quality metrics use Generated Subset only.

## 26. Statistical Analysis
McNemar's test for paired binary outcomes (if N_generated > 30). Descriptive comparison otherwise.

## 27. Missing Data
Cases missing due to provider failure are excluded from generation quality comparison.

## 28. Provider Failure Handling
Logged with error class.

## 29. Stopping Criteria
10 consecutive provider failures aborts the run.

## 30. Acceptance Criteria
Arm A and Arm B must both achieve a minimum of 60 successful generations to allow meaningful comparison.

## 31. Reproducibility Requirements
All hashes must match V1.2.

## 32. Clinical Correctness Limitation
Medical Correctness Not Measured.

## 33. Security and Credential Rules
No secrets in logs.

## 34. Artifact Freezing
Directory experiments/runs/real-llm-v1_3/REAL_LLM_V1_3_RUN_001.

## 35. V1.3 Limitations
Subject to provider stability.
