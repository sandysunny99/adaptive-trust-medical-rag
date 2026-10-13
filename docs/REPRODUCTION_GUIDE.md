# Reproduction Guide

## Scope

This guide reproduces deterministic engineering validation without making live
provider requests or modifying frozen research assets. The current evidence
package is `reports/audit/VALIDATION_PACKAGE_2026-10-13.md`.

## Prerequisites

- Python 3.12 and `uv`.
- Node.js/npm for the frontend.
- Dependencies installed from `uv.lock` and `frontend/package-lock.json`.
- Synthetic data only. Do not place PHI, credentials, or provider responses in
  the repository.

## Deterministic checks

Run from the repository root:

```powershell
$env:TESTING = "1"
uv run pytest -q
Set-Location frontend
npm test -- --run
npm run build
npm run lint
Set-Location ..
uv run ruff check src/adaptive_trust_medical_rag/services/live_application.py src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py tests/e2e/test_v6_c7_image_full_medical_rag.py
uv run bandit -r src -x tests -s B101,B105,B311,B404,B603,B607 -q
git diff --check
```

The expected current baseline is 1,211 backend tests passed with 4 skipped,
20 frontend tests passed, a successful frontend build, targeted Ruff/Bandit,
and no diff-check errors. Warnings do not count as scientific results.

## Frozen-artifact protection

Before and after any experiment, record SHA-256 hashes for the frozen
snapshots, manifests, prompts, and protocol files used by that experiment.
Restore only files that the test itself regenerated and never overwrite a
frozen input to make a test pass. The current observed hashes are recorded in
the validation package.

## Research gates

- Treat heuristic or generated labels as diagnostic-only until independently
  reviewed.
- Treat mocked provider results as deterministic engineering evidence only.
- Keep Free Replication V1 in `PREPARING` until the approved 200-case run has
  a reconciled ledger and immutable provider/protocol metadata.
- Keep live image extraction blocked until an authorized server-side provider
  credential is configured.
- Do not report superiority, clinical utility, or live security performance
  without valid case-level measurements and a preserved run manifest.

## Recovery

If a deterministic test regenerates known output files, stop and inspect
`git status`. Restore only the known generated files documented by the current
validation package. If a frozen input hash changes unexpectedly, stop the
experiment and report the mismatch; do not continue or amend the artifact.
