# NORMATIVE PROTOCOL TRACE

**Date:** 2026-10-03  
**Stage:** GATE B (Architecture Freeze)

## 1. Trace of Original Intent

A search across architecture and methodology documents yields the following about the original intent of the 9-factor model:

**Factually Established:**
- The 9 factors (including `query_relevance`, `evidence_quality`, and `anti_injection`) are formally defined in `trust.yaml`.
- The architecture explicitly establishes prompt injection and retrieval poisoning as separate vectors.
- Prompt injection is explicitly implemented as a separate hard downstream gate (`EvidenceEligibilityGate` calls `PromptInjectionDetector`).

**Research Gaps / Protocol Silence:**
- **Missing Values:** The normative protocol is entirely silent on what should happen if a factor cannot be measured. The current behavior (`MISSING=0.0`) is an implementation artifact of Python dataclass defaults, not an explicitly documented fail-closed safety rule.
- **Anti-Injection:** The protocol is ambiguous on whether `anti_injection` was intended to be a continuous trust probability or just a structural placeholder required to make the 9-factor math sum to 1.0.

## 2. Conclusion

Because the normative protocol does not define missing-value handling or the semantic role of anti-injection in the continuous score, these cannot be resolved by "fixing a bug." They are genuine research methodology gaps that must be defined by the researcher.
