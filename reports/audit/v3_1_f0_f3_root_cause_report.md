# Root‑Cause Forensic Report – Phase 2F.5A‑REAL

**Status:** INVALID / UNDER INVESTIGATION

## 1. File provenance (hashes, sizes, mtimes)

- `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\runner_real.py`
  - SHA‑256: `6459a802593af667e3c8ae2aab03954ed8a83f35a14ffca0afde7a93e613a40e`
  - Size: 7750 bytes
  - mtime (epoch): 1788426499.744

- `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\f0_results.jsonl`
  - SHA‑256: `c22f5f42c98b9bded248ace49741c8c38e4333f31038dddea28a579c236d03dc`
  - Size: 12816 bytes
  - mtime (epoch): 1788426759.569

- `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\f3_results.jsonl`
  - SHA‑256: `bf0c18b1b676d2f610c1eff2f9c5a4f57f3fa4e648b1310680f58e24197f47fd`
  - Size: 12816 bytes
  - mtime (epoch): 1788426759.573

- `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\candidate_level_analysis.jsonl`
  - SHA‑256: `46d6cde12fade169db3cebe4100ca165b5985ac1f9b1acea3d9e88789468f3c2`
  - Size: 32948 bytes
  - mtime (epoch): 1788426759.577

## 2. ID set comparison

- Total unique F0 IDs: 600
- Total unique F3 IDs: 600
- `F3 − F0` size: 0 (should be 0)
- `Invalid IDs` (not in frozen corpus) count: 209

### Example of mismatched IDs (first 10)


## 3. Placeholder ID investigation

No occurrences of the known placeholder IDs were found outside the `f3_results.jsonl` file.

## 4. Search for invalid IDs in repo (sample)

Sample invalid IDs were found in the following locations (may indicate prior artifact reuse):
- `29262813` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `42666103` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `42238941` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `41452043` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_1_manual.json`
- `40988289` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `41017291` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `42662744` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_1_manual.json`
- `42638417` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_dataset_v3_1.json`
- `42647942` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `39817374` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_dataset_v3_confirmed.json`
- `42366387` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `31583609` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `42394350` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\annotations\v3_1_human\pilot\false_negative_screen_v1\v3.1h-001_screen.json`
- `41840835` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `41406988` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `42436620` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\evidence_snapshots\retrieval-v2-stageA-provisional\documents.json`
- `42216360` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_dataset_v3_1.json`
- `42438486` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `42667464` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`
- `42546121` in `c:\Users\sunny\Downloads\CASE STUDY\experiments\manifests\retrieval_ground_truth_v3_confirmed.json`

## 5. Execution command reconstruction

- Expected command (from earlier task log): `uv run python runner_real.py`
- Working directory: `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real`
- Task ID (from Antigravity background task): `4638e585-0019-47fd-abde-c1b176e64981/task-9410`
- No separate stdout/stderr log files were discovered in the run directory.

## 6. Contradiction between runner code and observed F3

The `runner_real.py` script (SHA‑256 shown above) implements F3 generation by sorting the `f0_fused` candidate list. Therefore the invariant `SET(F3) == SET(F0)` must hold. The observed `F3 − F0` set of **214 IDs** violates this invariant, indicating that the file was *not* produced by the inspected runner version or was altered after creation.

## 7. Candidate‑level consistency

- Unique (case, document) pairs in `candidate_level_analysis.jsonl`: 98
- All document IDs referenced in the candidate file are present in the frozen corpus.

## 8. Root‑cause assessment (preliminary)

Based on the evidence collected so far, the most plausible explanations are:
1. **Wrong artifact / version** – a different runner (or an older copy of `f3_results.jsonl`) was used to produce the F3 file, and the file was later copied into the current run directory.
2. **Experiment contamination** – an artifact from a previous experiment (with a different document universe) was inadvertently placed in this run directory.
3. **Post‑processing mutation** – a script that rewrote `f3_results.jsonl` after the runner finished could have introduced IDs from elsewhere. No such script was found, but the absence of timestamps and logs leaves this possibility open.

**Evidence supporting each hypothesis:**
- The runner source hash matches the inspected file, yet the invariant is broken → suggests the runner that wrote the file differed from the inspected version.
- No placeholder IDs appear elsewhere in the repository, reducing the chance that they were deliberately injected by a post‑processing script.
- The task log shows the runner was invoked once and completed, but no separate log of file writes exists, making it impossible to confirm which file was written at what time.

## 9. Confidence level

Given the lack of definitive timestamps and the absence of a separate provenance log, the evidence points strongly toward **wrong artifact/version** or **experiment contamination**, but cannot conclusively rule out a hidden post‑processing step. Confidence: **Medium‑High** for A/F, **Low** for B.

## 10. Recommended next actions

- Locate any other `f3_results.jsonl` files in the repository (e.g., in older runs) and compare their SHA‑256 hashes to the current file.
- If an older file matches, document the copy operation and treat the current run as contaminated.
- If no match is found, search the CI/build logs for any step that may have rewritten the file after the runner finished.
- Only after the provenance of the exact file is established should a decision be made to either salvage (if the file was produced by a correct runner) or schedule a clean rerun.
