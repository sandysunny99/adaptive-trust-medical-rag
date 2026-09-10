# Execution Provenance Report – Phase 2F.5A‑REAL

This report records the exact script files and timestamps that produced the F0/F3 artefacts. It is intended for forensic root‑cause analysis.

## Files and hashes

- **c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\runner_real.py**
  - SHA‑256: `6459a802593af667e3c8ae2aab03954ed8a83f35a14ffca0afde7a93e613a40e`
  - Size: 7750 bytes
  - Modification time (epoch): 1788426499.744

- **c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\f0_results.jsonl**
  - SHA‑256: `c22f5f42c98b9bded248ace49741c8c38e4333f31038dddea28a579c236d03dc`
  - Size: 12816 bytes
  - Modification time (epoch): 1788426759.569

- **c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\f3_results.jsonl**
  - SHA‑256: `bf0c18b1b676d2f610c1eff2f9c5a4f57f3fa4e648b1310680f58e24197f47fd`
  - Size: 12816 bytes
  - Modification time (epoch): 1788426759.573

- **c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\candidate_level_analysis.jsonl**
  - SHA‑256: `46d6cde12fade169db3cebe4100ca165b5985ac1f9b1acea3d9e88789468f3c2`
  - Size: 32948 bytes
  - Modification time (epoch): 1788426759.577

## Execution context (best‑effort reconstruction)

- **Working directory**: `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real`
- **Command executed**: `uv run python runner_real.py` (as logged by the original launch)
- **Stdout / Stderr**: No separate log files were found in the run directory. The terminal output was captured by the Antigravity task system and is reflected in the task log (see the background task output).
- **Task identifier**: The Antigravity background task ID was `4638e585-0019-47fd-abde-c1b176e64981/task-9410` (see earlier run).
- **Execution timestamp**: Approximate start time recorded in the task log – `2026-09-03T14:55:53+05:30` (UTC+5:30).

## Consistency check

The runner implementation (see `runner_real.py`) sorts `f0_fused` to produce `f3_ranked_ids`. Therefore the set of document IDs in `f3_results.jsonl` should be a subset of (and equal to) those in `f0_results.jsonl`.

**Observed discrepancy:** 214 document IDs appear in `f3_results.jsonl` that are not present in the frozen corpus and not in `f0_results.jsonl`. This violates the expected invariant.

## Next steps (as per user instruction)

- Preserve the original run directory as immutable forensic evidence (`...-real-invalid/`).
- Perform root‑cause analysis using the invalid‑ID CSV and repository search.
- Do **not** modify any of the above artefacts until the cause is identified.
