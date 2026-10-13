# End-to-End Security Evaluation

**Audit date:** 2026-10-13
**Status:** Deterministic engineering coverage verified; live generative evaluation blocked

## Current controls

The live path now applies both provenance/hash validation and
`PromptInjectionDetector` to every retrieved evidence chunk before trust
scoring and generation. Evidence with injection markers, poisoning signals, or
hash mismatch is excluded. Provider transport failures remain separate from
medical evidence/security decisions.

Claim verification is fail-closed when claims are present: missing verifier,
empty/malformed verification output, or an exception cannot release an answer.
Canonical identity status and reason are preserved in the claim result.

## Case families and evidence

| Family | Deterministic coverage | Live-provider result |
|---|---|---|
| Prompt injection | adapter and E2E controls | Not run |
| Retrieval poisoning | tampered-hash E2E test | Not run |
| Boundary violation | security integration tests | Not run |
| Unsupported claim | claim-verifier tests | Not run |
| Contradiction | verifier/component tests | Not run |
| Benign control | image/manual happy-path tests | Not run with live provider |

The frozen security artifacts under `experiments/security_evaluation/` remain
unchanged. Existing Phase 13/14/15 reports are not relabeled as full
end-to-end generative validation.

## Verification

Focused image/security/provider regression run: **61 passed, 182 warnings,
exit code 0**. This demonstrates engineering behavior only; it does not
measure attack success rate, unsafe answer rate, or benign-case preservation
for a live model.

## Blocker

The authorized live provider configuration and the required evaluation approval
are unavailable. A valid experiment requires the frozen case manifest, fixed
provider/model, complete per-case ledger, and researcher authorization.
