# Real-LLM Dataset Authorization Reconciliation V1

## Dataset Profile
- **Dataset**: experiments/manifests/v3_1_human_cases.json
- **Dataset Hash**: db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc
- **Case Count**: 80
- **Case IDs Hash**: bb47d3c18a0c9bf5488437bc0bca873c4cd5ee4a2d6c7f8ce133ac6cd505da2f
- **Duplicates**: 0

## Original vs Proposed Purpose
- **Original Purpose**: Evaluating retrieval engines using document-level relevance and evidence spans.
- **Proposed Purpose**: Evaluating real-LLM generative claim support, abstention, and citation validity.
- **Answer Ground Truth**: NOT_AVAILABLE. The dataset provides query and relevance metadata but lacks explicit medical answer references.

## Metric Fit
1. claim_support_rate: **PARTIALLY_SUPPORTED**
2. citation_validation_rate: **SUPPORTED**
3. unsupported_answer_rate: **PARTIALLY_SUPPORTED**
4. bstention_rate: **PARTIALLY_SUPPORTED**
5. provider_failure_rate: **SUPPORTED**

## Arm Compatibility Audit
**PROTOCOL_REVISION_REQUIRED = TRUE**
The frozen protocol claims a "Single Intended Difference" between ARM A and ARM B. However, ARM B enables three coupled mechanisms: Trust Control, Controlled Abstention, and Claim Verification. Scientifically, this is an INTEGRATED_ADAPTIVE_TRUST_AWARE_EVIDENCE_CONTROL_LAYER. 
**Recommendation**: Revise the V1 protocol wording to explicitly state the experimental factor is the integrated control layer rather than a single component, avoiding false causal attribution.

## Conclusion
**DATASET_AUTHORIZATION = PENDING_RESEARCHER_DECISION**
Execution remains strictly blocked. Explicit researcher authorization is required to use this retrieval dataset for generation metrics.
