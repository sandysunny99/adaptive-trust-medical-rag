# RxNorm Validation Report

**Audit date:** 2026-10-13
**Status:** Engineering verified; scientific accuracy not measured

## Current path

Image candidates are explicitly confirmed before
`DrugNormalizer.normalize_batch()` is called. The normalizer resolves local
cache entries first, then exact RxNorm, then approximate RxNorm, and otherwise
returns an unresolved entity with confidence `0.0`. The live route blocks
downstream retrieval when any confirmed medication is unresolved or ambiguous.

## Confirmed remediation

Approximate RxNorm results have confidence `0.8` and are now classified as
`AMBIGUOUS` in the live workflow (`confidence <= 0.8`), rather than being
reported as fully matched. Exact/cache results remain `MATCHED` at confidence
`1.0`.

Canonical names, RxCUIs, formulations, and confidence are used for retrieval
query construction and entity matching. Matching uses escaped word boundaries,
not unrestricted substring checks. Claim verification continues to receive the
RxCUI map and now exposes canonical identity status and reason in claim output.

## Covered cases

| Case | Status | Evidence |
|---|---|---|
| Generic name | Verified | `tests/test_drug_normalizer.py` |
| Brand to generic (`Coumadin` → warfarin) | Verified | cache and live E2E tests |
| Salt/formulation separation | Verified | tartrate/succinate tests |
| Exact RxNorm fallback | Verified | mocked adapter test |
| Approximate match ambiguity | Engineering verified | confidence boundary in live route |
| Unknown name | Verified | controlled-abstention E2E test |
| User-confirmed image candidate | Verified | image confirmation E2E suite |
| Scientific canonicalization accuracy | Not measured | no labeled accuracy set authorized |

## Limitations

The repository does not contain a complete labeled medication-entity benchmark,
so no precision/recall or clinical accuracy claim is made. RxNorm network
availability and provider credentials are separate from deterministic
normalization tests.
