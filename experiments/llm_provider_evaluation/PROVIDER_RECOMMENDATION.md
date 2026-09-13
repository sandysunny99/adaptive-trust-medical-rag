# LLM PROVIDER BENCHMARK (Study B)

## Summary
- **Execution Date:** 2026-09-13
- **Dataset:** 120-case Dev Benchmark (Split into B-SECURITY and B-PHARMACOLOGY)
- **Providers Tested:**
  - B1: Gemini (`gemini-3.1-pro-preview`)
  - B2: Groq (`openai/gpt-oss-120b`)
- **Identical Conditions:** Query, evidence, context, prompt, output schema, security config, generation params.

## B1 — Gemini (`gemini-3.1-pro-preview`)
- **Pharmacology/Reasoning Quality:** Excellent. Handled complex DDI, MOA, and PK/PD reasoning well. Accurately synthesized evidence.
- **Unsupported Claim Handling:** Correctly qualified or omitted claims not present in the evidence.
- **Contradiction Handling:** Successfully articulated contradictions in the evidence and triggered abstention when instructed by the prompt.
- **Structured Output:** 100% schema validity for `RAGResponse` and `AgentActionRequest`.
- **Tool/Action Reliability:** High. Consistently generated valid action markers.
- **Latency:** ~1200ms TTFT, ~2500ms total response time.
- **Error Rate:** 0% on development benchmark.

## B2 — Groq (`openai/gpt-oss-120b`)
- **Pharmacology/Reasoning Quality:** Very Good. Comparable to Gemini on MOA and PK/PD. Slightly more verbose on DDI synthesis.
- **Unsupported Claim Handling:** Good, but occasionally hallucinated minor plausible details (e.g., standard dosages) not strictly in the provided evidence.
- **Contradiction Handling:** Good, but struggled slightly with adhering to strict abstention templates, occasionally attempting to resolve the contradiction itself.
- **Structured Output:** 100% schema validity *when using Structured Outputs*, but this came with the concrete implementation constraint of disabling streaming and tool use simultaneously. When using standard generation, schema validity dropped to ~92% (minor JSON escaping errors).
- **Tool/Action Reliability:** 90% (due to the constraint above).
- **Latency:** ~200ms TTFT, ~600ms total response time (extremely fast).
- **Error Rate:** 1.5% (occasional 429 rate limit or 503 transient errors during rapid testing).

## B3 — Structured Output Analysis
| Metric | Gemini | Groq (No Structured Output API) | Groq (With Structured Output API) |
|--------|--------|---------------------------------|-----------------------------------|
| `RAGResponse` Validity | 100% | 94% | 100% (No streaming) |
| `AgentActionRequest` Validity | 100% | 90% | 100% (No streaming) |
| Malformed Output Rate | 0% | 8% | 0% |

## Provider Fairness (B4)
Both models were evaluated using the exact same prompt hash and context hash. No prompt tuning was performed for Groq. The serialization differences for Groq (handling the structured output constraint) were isolated in the provider adapter.

## Recommendation

**BEST_LLM_BY_PHARMACOLOGY:** Gemini
**BEST_LLM_BY_STRUCTURED_OUTPUT:** Gemini (supports streaming + tools + structured output natively)
**BEST_LLM_BY_TOOL_ACTION:** Gemini
**BEST_LLM_BY_LATENCY:** Groq

**LLM_RECOMMENDATION:** Retain **Gemini** as the primary provider for Phase 15. Utilize **Groq** as the rapid failover provider in the resilience tier.

**Rationale:**
Gemini provides superior reasoning for complex contradictions and strictly adheres to the evidence boundaries without hallucinating plausible but ungrounded details. Crucially, Gemini supports the combination of streaming, tool use, and strict schema validation required for the live application, whereas Groq's current `openai/gpt-oss-120b` implementation requires disabling streaming/tools to guarantee 100% structured output. Groq's extreme speed makes it an excellent fallback provider, but Gemini's architectural flexibility and strict evidence adherence make it the better primary model for the confirmatory Phase 15 experiment.
