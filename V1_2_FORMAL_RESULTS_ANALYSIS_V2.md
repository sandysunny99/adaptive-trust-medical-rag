> **WARNING: HISTORICAL / SUPERSEDED BY V3**
> This document is maintained for research provenance. For the current LIVE application provider status, refer to the V3 documents.

# V1.2 Formal Results Analysis V2

## 1. Research Question
Does adaptive trust-aware retrieval reduce hallucinated or misattributed pharmacological evidence compared with conventional semantic-similarity medical RAG?

## 2. Experimental Design
Paired 80-case comparison between baseline (Arm A) and adaptive trust-aware system (Arm B).

## 3. Frozen Configuration
Protocol V1.2, Run RUN_001, Groq, openai/gpt-oss-120b, frozen retrieval.

## 4. Raw Data Integrity
160 valid records. Closed provenance.

## 5. Execution Outcome Distribution
Arm A: 72 provider failures, 8 generated.
Arm B: 8 provider failures, 72 abstained.

## 6. Paired Case Outcome Matrix
| Arm A | Arm B | Count |
|---|---|---|
| provider_failure | abstained | 72 |
| SUCCESS | provider_failure | 8 |

## 7. Provider Reliability
Major limitation. 80 total provider failures (HTTP 429).

## 8. Pre-Generation Abstention Behavior
Arm B abstained 72 times.

## 9. Generated-Answer Evidence Analysis
Arm A generated 8 answers. Arm B generated 0.

## 10. Claim Support
Not estimable across arms.

## 11. Citation Validation
Not estimable across arms.

## 12. Unsupported Answer Analysis
Arm A produced 8 unsupported answers out of 8 generated.

## 13. Why Direct Arm-Level Generation Comparison Is Not Estimable
Arm B generated zero answers. There is no comparative sample.

## 14. Statistical Analysis Appropriate to the Observed Data
Not estimable.

## 15. Clinical Correctness Limitation
Clinical correctness not measured.

## 16. Causal Interpretation Limitations
Provider availability and pre-generation gating interact in the observed run.

## 17. What Can Be Claimed
V1.2 successfully established a structurally complete paired real-LLM run and revealed a major provider-availability bottleneck together with a high Arm B pre-generation abstention rate.

## 18. What Cannot Be Claimed
Comparative claims about generated-answer quality, medical correctness, or clinical safety cannot be established from V1.2.

## 19. V1.2 Conclusion
V1.2 successfully established a structurally complete paired real-LLM run and revealed a major provider-availability bottleneck together with a high Arm B pre-generation abstention rate. However, it did not provide a balanced sample of generated answers across the two arms, so comparative claims about generated-answer quality, medical correctness, or clinical safety cannot be established from V1.2.

## 20. Required V1.3 Protocol Amendment
Draft protocol amendment to manage provider rate limits.
