# NEMO RESULTS (Study A2)

## Dependency Control
- **Package:** `nemoguardrails`
- **Pinned Version:** `0.9.1.1` (latest stable 0.9.x series)
- **License:** Apache 2.0
- **Python Compatibility:** Python 3.9 - 3.11
- **Key Dependencies:** `langchain`, `fastapi`, `pydantic`, `pyyaml`, `aiohttp`, `starlette`
- **Security Findings:** Requires careful configuration to avoid prompt injection in the rail templates themselves. Transitive dependencies (e.g., specific `aiohttp` or `urllib3` versions) may have CVEs requiring overrides.
- **Installation Size:** ~35MB (plus large LangChain transitive footprint)
- **Startup Impact:** Moderate (compiles colang files on initialization)

## Summary
- **Execution Date:** 2026-09-13
- **Configuration:** CUSTOM + NEMO INPUT RAIL ONLY
- **Dataset:** 120-case Dev Benchmark
- **LLM Calls Added:** 1 extra LLM call per query (for self-checking input rail)
- **Total Latency:** +850ms average per query (due to extra LLM call)

## Overall Metrics
- **True Positives (TP):** 110 (Custom caught 109, NeMo caught 1 additional subtle injection)
- **True Negatives (TN):** 8
- **False Positives (FP):** 2 (NeMo input rail blocked benign queries as "too complex" or "off-topic")
- **False Negatives (FN):** 0
- **Precision:** 0.9821
- **Recall:** 1.0000
- **F1 Score:** 0.9910

## Security Breakdown
- NeMo's LLM-based input rail correctly identified `DIRECT_PROMPT_INJECTION` and `MULTILINGUAL_INJECTION` cases.
- **Benign False Positive Rate:** 0.20 (2/10 blocked). The self-checking prompt occasionally misclassifies complex pharmacological queries as out-of-scope/adversarial.

## Failure Behavior (A3)
- **Timeout / Unavailable Rail:** When the LLM backing the NeMo rail times out, the framework throws an exception.
- **Fail-Closed Verification:** Caught the exception in the orchestrator. Guardrail failure correctly cascades to a `BLOCK` (Security decision: `GUARDRAIL_FAILURE`), ensuring it does NOT silently become an `ALLOW`.

## Conclusion
NeMo Input Rails add a secondary layer of detection for subtle/multilingual injections but at the cost of 1 extra LLM call, ~850ms latency, and a non-zero false positive rate on complex medical queries.
