# V1.2 Formal Results Analysis

## 1. Experiment Identity
- Protocol: REAL_LLM_EVALUATION_PROTOCOL_V1_2
- Run: REAL_LLM_V1_2_RUN_001
- Dataset: v3_1_human_cases.json
- Prompt: REAL_LLM_EVALUATION_PROMPT_V1_2.txt
- Provider: Groq
- Model: openai/gpt-oss-120b
- Retrieval: FROZEN_HISTORICAL_OUTPUT
- Temperature: 0
- Planned Requests: 160

## 2. Data Integrity
- Total records: 160
- Unique IDs: 160
- Duplicates: 0
- Missing pairs: 0
- Malformed records: 0
- Hash verification: PASS

## 3. Execution Reliability
- Provider success: 8 (Arm A)
- Provider failures: 80 (72 Arm A, 8 Arm B)
- Abstentions: 72 (0 Arm A, 72 Arm B)
- Failure types: HTTP 429 Rate Limit

## 4. Arm A Results
- Claim Support Rate: 0.00%
- Citation Validation Rate: 0.00%
- Unsupported Answer Rate: 10.00% (8/80 cases had unsupported answers generated)
- Abstention Rate: 0.00%
- Provider Failure Rate: 90.00%

## 5. Arm B Results
- Claim Support Rate: 0.00%
- Citation Validation Rate: 0.00%
- Unsupported Answer Rate: 0.00%
- Abstention Rate: 90.00%
- Provider Failure Rate: 10.00%

## 6. Paired Case Comparison
In 72 cases, Arm A suffered a provider failure while Arm B abstained pre-generation due to low trust scores. In 8 cases, Arm A successfully generated an answer (which turned out to be unsupported), while Arm B suffered a provider failure (since it passed the eligibility gate and attempted to query the API).

## 7. Claim Support
Claim support could not be meaningfully compared because Arm A's generated answers had 0% claim support, and Arm B generated 0 answers. CLAIM SUPPORT RATE IS NOT MEDICAL CORRECTNESS.

## 8. Citation Validation
Citation validation was 0% across both arms. Citations were either invalid, hallucinated, or non-existent in the few generated answers.

## 9. Unsupported Answers
Arm A produced 8 answers, all of which contained unsupported claims. Arm B produced no unsupported answers because it abstained from answering.

## 10. Abstention
Arm B abstained 90% of the time. ABSTENTION RATE MEASURED, ABSTENTION CORRECTNESS NOT MEASURED.

## 11. Statistical Comparison
Due to the overwhelming provider failure rate (90% in Arm A) and abstention rate (90% in Arm B), there is insufficient data to perform a meaningful statistical comparison of generation quality (e.g., McNemar's test for claim support).

## 12. Provider Failure Impact
Provider failures masked the true behavior of the system. In Arm A, 90% of requests failed due to rate limits. If the API had been stable, Arm A would likely have produced 80 generated answers.

## 13. Research Limitations
See V1_2_RESEARCH_LIMITATIONS.md. The primary limitations are a 50% overall provider failure rate and the lack of medical ground truth.

## 14. What Can Be Claimed
- The Adaptive Trust Scorer (Arm B) effectively limits API calls when evidence is deemed untrustworthy, resulting in a high abstention rate (90%).
- The baseline system (Arm A), when it successfully connects to the API, is prone to generating unsupported answers (8/8 cases).

## 15. What Cannot Be Claimed
- "Arm B is medically more accurate" (clinical correctness not measured).
- "Arm B is clinically safer" (safety implies real-world correctness).
- "The system detects all unsafe answers" (insufficient data).

## 16. Research Conclusion
The V1.2 experiment execution highlights severe provider reliability issues and strict pre-generation gating. The baseline system (Arm A) generated exclusively unsupported claims when it successfully ran, while the Adaptive Trust-Aware system (Arm B) heavily preferred abstention, shielding the system from generating hallucinations but severely limiting overall recall. Further research with a stable, rate-limit-free provider is necessary to evaluate the post-generation safety gate.
