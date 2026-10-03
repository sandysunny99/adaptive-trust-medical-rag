# Real-LLM Evaluation Protocol V1.1

## Objective
Evaluate the INTEGRATED_ADAPTIVE_TRUST_AWARE_EVIDENCE_CONTROL_LAYER as a system factor using a real LLM generation backend (Groq: openai/gpt-oss-120b). Measure claim grounding, citation validity, and observed controlled abstention against a standard baseline.

**Scientific Interpretation Notice**: This experiment compares a baseline pipeline and an integrated control layer. It does NOT isolate the causal effect of each individual mechanism (e.g., trust scoring alone), nor does it establish clinical correctness, clinical utility, provider superiority, or universal hallucination reduction.

## Dataset & Authorization
- **Dataset Path**: experiments/manifests/v3_1_human_cases.json
- **Case Count**: 80
- **Dataset Hash**: db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc
- **Case IDs Hash**: bb47d3c18a0c9bf5488437bc0bca873c4cd5ee4a2d6c7f8ce133ac6cd505da2f
- **Answer-Level Medical Ground Truth**: NOT_AVAILABLE (The dataset was originally designed for retrieval/evidence evaluation).
- **Authorization Status**: PENDING_RESEARCHER_DECISION (Execution is BLOCKED).

## Experimental Arms
### ARM_A_BASELINE
- **Description**: Baseline RAG pipeline. Trust scoring and safety gates disabled.

### ARM_B_ADAPTIVE
- **Description**: Full Adaptive Trust-Aware pipeline.
- **Experimental Factor**: INTEGRATED_ADAPTIVE_TRUST_AWARE_EVIDENCE_CONTROL_LAYER (Trust Control, Controlled Abstention, and Claim Verification). All prompt, ordering, retrieval evidence, and model configs are identical.

## Metrics
Since answer-level ground truth is unavailable, metrics evaluate evidence/claim support, NOT clinical correctness:
1. **claim_support_rate**: Proportion of generated factual claims successfully verified against cited retrieved evidence under the existing Claim Verification implementation.
2. **citation_validation_rate**: Proportion of explicit citations that map to valid retrieved chunks.
3. **unsupported_answer_rate**: Proportion of answers containing at least one UNSUPPORTED_OR_UNVERIFIED_CLAIM.
4. **abstention_rate**: OBSERVED_ABSTENTION_RATE only (correctness cannot be measured without ground truth).
5. **provider_failure_rate**: Provider failures / total authorized provider requests.

## Policies
- **Failure Handling**: Provider failures are explicitly recorded. No retries, no imputation, no fallback.
- **Retrieval Scope**: FROZEN HISTORICAL OUTPUT.
- **Security Scope**: EXCLUDED.
- **Request Budget**: 160 requests maximum.
