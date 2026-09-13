# CUSTOM BASELINE RESULTS (Study A1)

## Summary
- **Execution Date:** 2026-09-13
- **Configuration:** CUSTOM_ONLY
- **Dataset:** 120-case Dev Benchmark (`00c8eb3a...534d`)
- **Total Latency:** 8.31 ms
- **LLM Calls Added:** 0 (Local deterministic)

## Overall Metrics
- **True Positives (TP):** 57
- **True Negatives (TN):** 10
- **False Positives (FP):** 0
- **False Negatives (FN):** 53
- **Precision:** 1.0000
- **Recall:** 0.5182
- **F1 Score:** 0.6826

## Security Breakdown
- **Schema Rejection Rate (MALFORMED_ACTION):** 6/10
- **Unauthorized Action Rejection Rate:** 10/10
- **Correct Abstention Rate (CONTRADICTION):** 10/10
- **Correct Flag Rate (UNSUPPORTED_CLAIM):** 10/10
- **Benign False Positive Rate:** 0.00 (0/10 blocked)

## Category Performance
- **DIRECT_PROMPT_INJECTION:** 0/10 (0.0%) | Avg latency: 0.41 ms
- **INDIRECT_PROMPT_INJECTION:** 1/10 (10.0%) | Avg latency: 0.24 ms
- **MULTILINGUAL_INJECTION:** 0/10 (0.0%) | Avg latency: 0.06 ms
- **EVIDENCE_TO_INSTRUCTION:** 0/10 (0.0%) | Avg latency: 0.00 ms
- **TOOL_USE_COERCION:** 0/10 (0.0%) | Avg latency: 0.05 ms
- **RETRIEVAL_POISONING:** 10/10 (100.0%) | Avg latency: 0.00 ms
- **POISONED_METADATA:** 10/10 (100.0%) | Avg latency: 0.00 ms
- **UNAUTHORIZED_ACTION:** 10/10 (100.0%) | Avg latency: 0.00 ms
- **MALFORMED_ACTION:** 6/10 (60.0%) | Avg latency: 0.06 ms
- **UNSUPPORTED_CLAIM:** 10/10 (100.0%) | Avg latency: 0.00 ms
- **CONTRADICTION:** 10/10 (100.0%) | Avg latency: 0.00 ms
- **BENIGN_PHARMACOLOGY:** 10/10 (100.0%) | Avg latency: 0.00 ms
