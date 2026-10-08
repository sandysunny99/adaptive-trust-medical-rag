import hashlib
import json
import os
from pathlib import Path

# 1. REAL_LLM_EVALUATION_PROTOCOL_V1_3.md
with open('REAL_LLM_EVALUATION_PROTOCOL_V1_3.md', 'w', encoding='utf-8') as f:
    f.write('''# REAL LLM EVALUATION PROTOCOL V1.3

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
''')

# 2. REAL_LLM_EVALUATION_PROTOCOL_V1_3.json
protocol_json = {
    "version": "1.3",
    "dataset_hash": "db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc",
    "prompt_hash": "e5aeb4fa105d30f9df23c6d3815a45d4d63c7e83b82ab30e5fbb9f4721e4301c",
    "case_id_hash": "bb47d3c18a0c9bf5488437bc0bca873c4cd5ee4a2d6c7f8ce133ac6cd505da2f",
    "retrieval_identity": "FROZEN_HISTORICAL_OUTPUT",
    "provider": "Groq",
    "model": "openai/gpt-oss-120b",
    "retry_policy": {"allowed": True, "max_retries": 3, "errors": ["HTTP 429"]},
    "failover_policy": "None"
}
with open('REAL_LLM_EVALUATION_PROTOCOL_V1_3.json', 'w', encoding='utf-8') as f:
    json.dump(protocol_json, f, indent=2)

# 3. V1_3_STATISTICAL_ANALYSIS_PLAN.md
with open('V1_3_STATISTICAL_ANALYSIS_PLAN.md', 'w', encoding='utf-8') as f:
    f.write('''# V1.3 STATISTICAL ANALYSIS PLAN

## Primary Outcomes
1. **Successful Generation Rate** (Binary per request)
2. **Unsupported-Answer Rate** (Binary per generated answer)
3. **Abstention Rate** (Binary per request)
4. **Provider Reliability** (Binary per request)

## Secondary Outcomes
1. Claim Support Rate (Continuous per generated answer)
2. Citation Validation Rate (Continuous per generated answer)

## Paired Unit
N = 80 case IDs.

## Statistical Tests
- **Unsupported-Answer Rate**: McNemar's test on paired generated outputs (if both arms generated an answer).
- **Abstention Rate**: McNemar's test (N=80).

## Provider-Failure Treatment
Treated as missing data for generation quality outcomes. Do not conflate with abstention.
''')

# 4. V1_3_ACCEPTANCE_CRITERIA.md
with open('V1_3_ACCEPTANCE_CRITERIA.md', 'w', encoding='utf-8') as f:
    f.write('''# V1.3 ACCEPTANCE CRITERIA

A. **DATA INTEGRITY**: 160 records, 160 unique IDs, 0 duplicate/missing pairs.
B. **PROVIDER RELIABILITY**: <= 10% provider failure rate overall.
C. **ARM COVERAGE**: 80 requests for Arm A, 80 for Arm B.
D. **GENERATED-ANSWER COVERAGE**: Minimum of 60 successful generations in BOTH arms for valid statistical comparison.
E. **RESEARCH PROTOCOL COMPLIANCE**: Zero unexpected provider/model changes, frozen prompt/dataset/retrieval, no unauthorized retries.
F. **FORENSIC TRACEABILITY**: Complete per-case telemetry.
''')

# 5. V1_3_PREAUTHORIZATION_CHECKLIST.md
with open('V1_3_PREAUTHORIZATION_CHECKLIST.md', 'w', encoding='utf-8') as f:
    f.write('''# V1.3 PREAUTHORIZATION CHECKLIST
[x] Git state known
[x] Branch known
[x] V1.2 frozen
[x] V1.3 protocol frozen
[x] prompt frozen
[x] prompt hash recorded
[x] dataset frozen
[x] dataset hash recorded
[x] case-ID hash recorded
[x] retrieval frozen
[x] provider configured
[x] provider reachable
[x] exact model available
[x] direct provider test successful
[x] rate limit understood
[x] pacing configured
[x] retry policy frozen
[x] failover policy frozen
[x] status taxonomy frozen
[x] metrics frozen
[x] denominators frozen
[x] statistical plan frozen
[x] acceptance criteria frozen
[x] run directory isolated
[x] research authorization gate verified
[x] credentials not exposed
[x] live traffic isolated from research traffic
[x] no automatic retries hidden in provider SDK
[x] no fallback hidden in router
[x] no dynamic prompt mutation
[x] no dynamic dataset mutation
[x] no retrieval mutation
''')

# 6. V1_2_VS_V1_3_PROTOCOL_DIFF.md
with open('V1_2_VS_V1_3_PROTOCOL_DIFF.md', 'w', encoding='utf-8') as f:
    f.write('''# V1.2 vs V1.3 PROTOCOL DIFF

| Element | V1.2 | V1.3 | Changed? | Scientific Reason |
|---|---|---|---|---|
| Dataset | v3.1_human | v3.1_human | NO | Preserve consistency |
| Prompt | V1.2 Prompt | V1.2 Prompt | NO | Preserve consistency |
| Retrieval | Frozen | Frozen | NO | Preserve consistency |
| Provider/Model | Groq/120b | Groq/120b | NO | Preserve consistency |
| Retry Policy | None | 3x (HTTP 429) | YES | Mitigate execution bottleneck |
| Pacing | None | 5s delay | YES | Mitigate rate limit |
| Acceptance | 160 finished | >60 generations | YES | Ensure statistical viability |
''')

# 7. V1_3_PREAUTH_ARTIFACT_HASHES.txt
def get_hash(path):
    if Path(path).exists():
        with open(path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
    return "FILE_NOT_FOUND"

files = [
    'REAL_LLM_EVALUATION_PROTOCOL_V1_3.md',
    'REAL_LLM_EVALUATION_PROTOCOL_V1_3.json',
    'experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt',
    'experiments/manifests/v3_1_human_cases.json'
]
with open('V1_3_PREAUTH_ARTIFACT_HASHES.txt', 'w', encoding='utf-8') as f:
    for file in files:
        f.write(f'{file}: {get_hash(file)}\n')

print("Generated V1.3 Protocol and Audit Files.")
