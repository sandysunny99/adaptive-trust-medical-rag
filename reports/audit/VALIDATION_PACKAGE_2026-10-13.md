# Deterministic Validation Package — 2026-10-13

## Repository state

- Repository: `sandysunny99/adaptive-trust-medical-rag`
- Branch: `sandysunny99-implement-request`
- Validation source commit: `30dc4617554ef7254970b813e998afabd06423d0`
- Working tree: clean after restoring test-generated frozen outputs.
- No credentials or live provider requests were used.

## Engineering validation

| Command | Result |
|---|---|
| `$env:TESTING='1'; uv run pytest -q` | **1,211 passed, 4 skipped, 729 warnings**, exit 0 |
| `Set-Location frontend; npm test -- --run` | **20 passed across 4 files**, exit 0 |
| `Set-Location frontend; npm run build` | Passed |
| `Set-Location frontend; npm run lint` | Passed; one existing warning in `WorkspacePage.tsx` |
| `uv run ruff check src/adaptive_trust_medical_rag/services/live_application.py src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py tests/e2e/test_v6_c7_image_full_medical_rag.py` | Passed |
| `uv run bandit -r src -x tests -s B101,B105,B311,B404,B603,B607 -q` | Passed |
| `git diff --check` | Passed |

The broader exploratory command `uv run ruff check src tests scripts experiments`
still reports legacy style findings in historical experiment scripts. That
result is not conflated with the targeted remediation lint gate.

## Frozen-artifact hashes observed

These hashes were captured after the test run and after restoration of the
known generated outputs:

| Artifact | SHA-256 |
|---|---|
| `experiments/track_a_abstract_enriched_reannotation_v1/TRACK_A_ABSTRACT_ENRICHED_SOURCE_SNAPSHOT.jsonl` | `7675691b41e59e316bbbbde02a7d040b81f9f30c072e0a17f47fccbfb2a097ad` |
| `experiments/security_evaluation/FREEZE_MANIFEST_PHASE_13C.json` | `b2caae35c51adb8821f9bdb5737b65c2bf80f29e4b5fb60bf7bdd9f1a8651fe8` |
| `experiments/architecture_baseline/FREE_REPLICATION_V1_MANIFEST.json` | `5a91939f75ce1773991748595030f3c372e04c04acc8b5e5fb6cd6836c0ade9e` |
| `experiments/track_a_abstract_enriched_reannotation_v1/COGNEE_PHASE0_CORPUS_HASH.txt` | `3d23115cc7bdce25bc682fda7ec87fbc38147c76b3f9d8a9dc6da3c476ed039e` |

## Research validation boundary

- The strict V3.1 integrity script completed with `FAIL` because its ground
  truth is heuristic and lacks independent human review. It remains
  `AUTOMATED_DIAGNOSTIC_ONLY`; no benchmark superiority claim is supported.
- Free Replication V1 remains `PREPARING` with zero observations and zero
  provider calls.
- Live prescription-image extraction remains blocked by missing authorized
  provider configuration.
- Full live security evaluation, complete claim-evidence labels, and valid
  Cognee retrieval remain unproven.
- Existing historical reports with live-provider language are preserved but
  are not current evidence unless explicitly linked to the current revision.

## Reproduction

From the repository root:

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
uv run python scripts/verify_v3_1_integrity_strict.py
```

Do not run a live provider experiment until credentials, quota, model identity,
protocol approval, and output-location authorization are recorded.
