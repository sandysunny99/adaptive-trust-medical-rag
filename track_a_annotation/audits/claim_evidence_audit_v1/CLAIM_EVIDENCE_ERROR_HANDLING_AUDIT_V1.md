# ERROR-HANDLING AUDIT

- **NLI Inference Error**: `ClaimVerifierV2` catches `NLIInferenceError`, sets chunk scores to `neutral=1.0`, `ent=0, con=0`. This falls back to `INSUFFICIENT_EVIDENCE`. -> **FAIL-CLOSED**.
- **Malformed LLM Actions**: Orchestrator catches `ActionParseError` -> triggers `abstain`. -> **FAIL-CLOSED**.
- **Missing Citations**: Evaluated against all chunks. If entailed, `SUPPORTED`. -> **FAIL-OPEN (Provenance Gap)**.
