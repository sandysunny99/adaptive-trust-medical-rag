# Real-LLM Evaluation Protocol V1

## Objective
Evaluate the Adaptive Trust-Aware Evidence Control Layer using a real LLM generation backend (Groq: openai/gpt-oss-120b). Measure claim grounding, citation validity, and controlled abstention against a standard baseline.

## Dataset & Authorization
- **Dataset Path**: experiments/manifests/v3_1_human_cases.json
- **Case Count**: 80
- **Dataset Hash**: db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc
- **Authorization Status**: PENDING_RESEARCHER_DECISION (The dataset exists but lacks formal project documentation authorizing it specifically for Real-LLM medical evaluation).

## Provider & Generation
- **Provider**: Groq
- **Model**: openai/gpt-oss-120b
- **Temperature**: 0.0
- **Max Tokens**: None
- **Seed**: NOT_SUPPORTED
- **Strict Reproducibility**: FALSE

## Experimental Arms
### ARM_A_BASELINE
- **Description**: Baseline RAG pipeline with trust scoring and safety gates disabled.

### ARM_B_ADAPTIVE
- **Description**: Full Adaptive Trust-Aware pipeline with Evidence Eligibility and Answer Safety gates.
- **Single Intended Difference**: Trust/Abstention/Claim verification layer enabled. All prompt, ordering, retrieval evidence, and model configs are identical.

## Prompt Freeze
- **Version**: REAL_LLM_PROMPT_V1
- **Hash**: 1d461a83fd6ade33291ce565a0032cdb01c73d2b76386dc68c5dc12aa0970c09

## Metrics
1. **claim_support_rate**: Proportion of generated claims successfully verified against cited evidence.
2. **citation_validation_rate**: Proportion of generated citations that map to valid retrieved chunks.
3. **unsupported_answer_rate**: Proportion of answers containing at least one unsupported or unverified claim.
4. **abstention_rate**: Proportion of cases successfully triggering a controlled abstention.
5. **provider_failure_rate**: Proportion of provider network/quota/authentication failures.

## Policies
- **Retrieval Scope**: FROZEN HISTORICAL OUTPUT. Do not re-run BM25 or semantic search.
- **Security Scope**: EXCLUDED. Prompt Injection V1 remains a diagnostic tool.
- **Failure Handling**: Failed requests are explicitly marked and recorded, neither retried nor imputed.
- **Missing Factors**: Trust scorer retains missing factors explicitly. Missing = zero trust contribution.
- **Request Budget**: 80 cases * 2 arms * 1 repeat = 160 requests maximum.
