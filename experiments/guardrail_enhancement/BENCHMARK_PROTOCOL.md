# Guardrail Benchmark Protocol (Part 6)

## Overview
This protocol defines the independent development benchmark for evaluating the effectiveness, latency, and resource cost of open-source guardrail frameworks (NeMo Guardrails, Guardrails AI) vs the custom Adaptive Trust architecture.

## Dataset
- **Must NOT** use experiments/phase15/phase15_cases.jsonl.
- A dedicated synthetic development dataset (experiments/guardrail_enhancement/dev_benchmark.jsonl) will be used.

## Test Vectors
1. **Direct Prompt Injection**: User attempts to override the system prompt.
2. **Indirect Prompt Injection**: Retrieved evidence contains embedded instructions.
3. **Multilingual Injection**: Malicious instructions in non-English languages.
4. **Retrieval Poisoning**: Evidence with high computed anomaly scores.
5. **Unauthorized Action**: LLM generates an AgentActionRequest for a forbidden tool.
6. **Contradiction**: Retrieved documents have conflicting medical claims.
7. **Benign Pharmacology**: Standard R0/R1 medical queries to measure false-positive blocking.

## Metrics
- **Effectiveness**: True Positive (blocked malicious), True Negative (allowed benign), False Positive (blocked benign), False Negative (allowed malicious).
- **Latency**: End-to-end processing time (P50, P95).
- **Resource Cost**: Number of LLM API calls made per request.

## Execution Tracks
- **Track A**: Custom Core Only
- **Track B**: Custom + NeMo (Input Rails only)
- **Track C**: Custom + Guardrails AI (Output validation only)
