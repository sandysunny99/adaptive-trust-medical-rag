# Canonical Relationship Identity Abstention Specification V1

## 1. Mismatch Mapping
When the deterministic canonical identity check fails (e.g. `wrong direction`, `wrong pair`, `identity mismatch`), the state maps to `UNSUPPORTED`.
- **Why?** The existing Answer Safety Gate handles `UNSUPPORTED` by automatically triggering `Controlled Abstention` or qualifying the answer, preserving backward compatibility with the existing State Model.

## 2. Ambiguity Handling
When the generated claim cannot be parsed into a strict canonical format, or one entity cannot be uniquely mapped:
- The state maps to `UNSUPPORTED` (or `AMBIGUOUS`, which routes to `UNSUPPORTED` logic).
- **CRITICAL REQUIREMENT:** Unresolved canonical identity must *not* silently fall through to NLI and release the answer. It must be an explicit failure condition that reaches the existing abstention mechanism, preserving fail-closed behavior.

## 3. Conflict with Evidence (Adversarial)
If RG-02 status says `SUPPORTED` but the Canonical Check says `UNSUPPORTED` (because the NLI was spoofed by directionality hijacking or entity misattribution):
- The Canonical Check overrides RG-02 and NLI.
- State is forced to `UNSUPPORTED`.
- **Result:** `AnswerSafetyGate` triggers `ABSTAIN`.
