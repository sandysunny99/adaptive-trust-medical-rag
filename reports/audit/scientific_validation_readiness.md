# Scientific Validation Readiness

**Audit date:** 2026-10-13

## Status by research track

| Track | Status | Evidence | Next gate |
|---|---|---|---|
| Track 0 foundation/freeze | FROZEN | versioned manifests and historical reports | maintain hashes |
| Trust-score completeness | ENGINEERING VERIFIED | `TRUST_SCORE_COMPONENT_AUDIT.md`, focused tests | freeze factor measurement protocol |
| RxNorm/entity resolution | ENGINEERING VERIFIED | `RXNORM_VALIDATION_REPORT.md`, normalizer/E2E tests | labeled accuracy set |
| Track A human relevance | BLOCKED BY MISSING GROUND TRUTH | 530-position readiness artifacts | researcher annotation/adjudication |
| Abstract-enriched secondary study | PARTIALLY COMPLETE | 522 enrichable and 8 non-enrichable positions recorded | authorized annotation smoke test |
| Free Replication V1 | BLOCKED BY RESEARCHER AUTHORIZATION | manifest `PREPARING`, zero observations | approved 200-case run |
| Claim-evidence benchmark | PENDING | protocol, matrix, and metric definitions exist | verified labels and E2E provider |
| Security E2E | PARTIALLY COMPLETE | deterministic controls and frozen case sets | authorized live generative run |
| Provenance/entity/contradiction/freshness benchmarks | PENDING | component controls exist; no unified frozen benchmark | freeze schemas and labeled cases |
| Cognee Phase 0 | PARTIALLY COMPLETE | adapter and Gate 5 diagnostics | valid non-empty live search proof |
| Integrated scientific validation | NOT STARTED | prerequisites remain blocked | complete primary studies first |
| Thesis/paper conclusions | NOT READY | no valid complete primary result set | do not report superiority claims |

## Reproducibility

Known protected artifacts include the Track A snapshots, security freeze
manifest, Free Replication manifest/protocol, and Cognee Gate 5 failure
artifacts. They remain historical inputs/results and were not rewritten by this
remediation.

## Current deterministic validation

- `TESTING=1 uv run pytest -q` — **1,211 passed, 4 skipped, 729 warnings**, exit code 0.
- `Set-Location frontend; npm test -- --run` — **20 passed across 4 files**, exit code 0.
- `Set-Location frontend; npm run build` — passed.
- `Set-Location frontend; npm run lint` — passed with one existing warning.
- Targeted Ruff and Bandit — passed.
- `uv run python scripts/verify_v3_1_integrity_strict.py` — completed with `FAIL`; heuristic ground truth is correctly classified as diagnostic-only.
- No live provider request was issued.

## Disposition

**Engineering fixes complete; scientific validation still in progress.**
The repository is ready for human review with provider, authorization, and
ground-truth limitations.
