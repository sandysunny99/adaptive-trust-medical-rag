# GUARDRAILS AI RESULTS (Study A5)

## Dependency Control
- **Package:** `guardrails-ai`
- **Pinned Version:** `0.5.0`
- **License:** Apache 2.0
- **Python Compatibility:** Python 3.9 - 3.11
- **Key Dependencies:** `pydantic`, `tenacity`, `lxml`, `regex`, `rich`, `typing-extensions`
- **Security Findings:** Requires validator hub downloads at runtime by default (must be configured for offline/local use to prevent supply chain risks during execution).
- **Installation Size:** ~25MB
- **Startup Impact:** Low

## Summary
- **Execution Date:** 2026-09-13
- **Configuration:** CUSTOM + GUARDRAILS AI (Schema Validation Only)
- **Dataset:** 120-case Dev Benchmark (MALFORMED_ACTION focus)
- **LLM Calls Added:** 0 (using local schema validators)
- **Total Latency:** +15ms average per validation

## Overall Metrics (MALFORMED_ACTION Category)
- **True Positives (TP):** 10 (Schema rejections)
- **True Negatives (TN):** N/A (Evaluating schema validation on valid requests)
- **Schema Rejection Rate:** 10/10

## Comparison vs Custom (Pydantic)
- **Custom Pydantic Baseline:** Successfully caught all 10 malformed actions (invalid types, missing fields, excessive nesting, invalid JSON, SQL injection payload).
- **Guardrails AI:** Caught the same 10 malformed actions.
- **Benefit Analysis:** For pure structured output validation, Guardrails AI provides identical functional protection to strict Pydantic + standard JSON parsing. Its primary benefit lies in LLM-based factuality validators (which were not enabled per A5 rules) and auto-correction (which we explicitly disable in a medical context because we want to fail closed).

## Conclusion
Adding Guardrails AI purely for schema validation provides **no measurable benefit** over the existing strict Pydantic `AgentActionRequest` parser, while adding a dependency.
