# Guardrail Component Overlap Matrix (B5)

This matrix compares the custom medical RAG security components with capabilities provided by open-source guardrail frameworks (NeMo Guardrails, Guardrails AI).

| Capability | Custom | NeMo Guardrails | Guardrails AI | Decision | Justification |
|---|---|---|---|---|---|
| **Prompt Injection** | PromptInjectionDetector | Input Rails | Not Applicable | **DEFENSE-IN-DEPTH** | Use NeMo's broad NLP injection detection alongside the custom strict medical sanitization. |
| **Retrieval Poisoning** | RetrievalPoisoningDetector | Retrieval Rails | Not Applicable | **KEEP CUSTOM** | The custom implementation uses SHA-256 provenance hashes specific to the medical corpus. |
| **Trust/Authority** | AdaptiveTrustScorer | Not Applicable | Not Applicable | **KEEP CUSTOM** | Trust calculation based on RxNorm entities, FDA authority, and freshness is unique to this architecture. |
| **Evidence Eligibility** | EvidenceEligibilityGate | Not Applicable | Not Applicable | **KEEP CUSTOM** | Risk-tier thresholding is a core experimental treatment. |
| **Claim Verification** | ClaimVerifier | Output Rails | Response Validation | **KEEP CUSTOM** | Custom verifier uses specific medical NLI logic (contradiction vs neutral vs entailment). |
| **Contradiction Detection**| AnswerSafetyGate | Output Rails | Factual Consistency | **KEEP CUSTOM** | Must preserve the medical research rule of highlighting contradictions to the user. |
| **Abstention** | ControlledAbstention | Output Rails | Validation Failure | **KEEP CUSTOM** | Custom medical abstention templates (RESEARCH_DISCLAIMER) are legally/medically required. |
| **Authorization** | AuthorizationBoundary | Execution Rails | Not Applicable | **KEEP CUSTOM** | NeMo must NOT be allowed to bypass the custom tool execution boundary. |
| **Structured Output** | N/A | Output Rails | Schema Validation | **DEFENSE-IN-DEPTH** | Guardrails AI provides excellent structured output validation that could supplement base LLM parsing. |

**Summary**: 
NeMo and Guardrails AI will NOT replace the custom Adaptive Trust core. They will be evaluated purely as an outer defense-in-depth layer (e.g., standard prompt injection NLP models, schema validation) sitting around the custom core.
