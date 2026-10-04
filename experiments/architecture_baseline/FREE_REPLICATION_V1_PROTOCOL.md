# Free Replication V1 - Protocol

> [!IMPORTANT]
> This experiment is explicitly independent of canonical Phase 15. The purpose of this track is to evaluate whether the orchestrator's security architecture exhibits similar behavior when tested against a lower-tier/free-access provider model.

## 1. Experiment Identity
* **Experiment ID:** `FREE_REPLICATION_V1`
* **Protocol Hash:** (To be generated upon freeze)
* **Parent Dataset:** Reuses the frozen 200-case input benchmark from Phase 15 explicitly as an input reference.

## 2. Research Question
Does the medical RAG security architecture (dual gates, adaptive trust thresholds, contradiction detection) exhibit robust protective behavior when the language generation is performed by a freely accessible, alternative model provider configuration?

## 3. Provider and Model
* **Provider:** `groq`
* **Model:** `openai/gpt-oss-120b`
* **Access Level:** Free/Developer Tier (No payment).

## 4. Experimental Structure & Pair Integrity
* **Cases (N):** 200
* **Condition A (Baseline):** Security gates disabled (trust thresholds bypassed, post-gen validation disabled).
* **Condition B (Hardened):** Security gates fully active.
* **Pairing Unit:** Identical case execution across Condition A and B.
* **Pair Integrity:** A case is only `PAIRED_COMPLETE` if both Baseline and Hardened complete successfully. If one fails non-recoverably, the case state is `EXECUTION_FAILED`. Incomplete pairs must not be used for SFR/McNemar computation.

## 5. Structured Output and Tool Path Integration
FREE_REPLICATION_V1 uses the project's native agent/action execution semantics. Groq is accessed through the project LLM backend adapter, while action parsing, authorization, tool execution, security decisions, and auditing remain under the project's existing control path.
* **Protocol Requirement:** Provider-specific API capabilities not used by the existing orchestrator (e.g. OpenAI native `tool_calls`, second-stage structured JSON extraction) are not experimental requirements. The orchestrator extracts `[ACTION: TYPE ON DOMAIN]` tags from standard text completions.

## 6. Scientific Observation Rules
* **SMOKE_TEST_ONLY:** Preflight scripts verifying capability.
* **ACCESS_TELEMETRY_ONLY:** Quota polling requests.
* **EXECUTION_FAILURE:** Failed benchmark requests (e.g., persistent 400s or context limits).
* **SCIENTIFIC_OBSERVATION:** A valid, completed baseline/hardened case sequence.

## 7. Statistical Framework
* **Metric:** Safety Failure Rate (SFR)
* **Test:** Exact McNemar test for paired nominal data
* **Confidence Interval:** 95% Clopper-Pearson
* *Note: These are explicitly adopted for this new protocol and do not inherit canonical Phase 15's authority.*
