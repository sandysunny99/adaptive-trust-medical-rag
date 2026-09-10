# Forensic Reconciliation Report – Real Phase 2F.5A Run

## 1. Run identity
Original run directory: `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real`

## 2. Frozen corpus identity
Corpus file: `c:\Users\sunny\Downloads\CASE STUDY\experiments\evidence_snapshots\retrieval-v3-real\documents.json`
Corpus SHA‑256: e4346ad15ec1f74af9ecc010ef822503eb44638f1020e7f0fcb51ad5c58f42f7

## 3. Raw artifact provenance
- `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\f0_results.jsonl` – SHA256: c22f5f42c98b9bded248ace49741c8c38e4333f31038dddea28a579c236d03dc, size: 12816 bytes, mtime: 1788426759.569012
- `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\f3_results.jsonl` – SHA256: bf0c18b1b676d2f610c1eff2f9c5a4f57f3fa4e648b1310680f58e24197f47fd, size: 12816 bytes, mtime: 1788426759.5730097
- `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\candidate_level_analysis.jsonl` – SHA256: 46d6cde12fade169db3cebe4100ca165b5985ac1f9b1acea3d9e88789468f3c2, size: 32948 bytes, mtime: 1788426759.5770226
- `c:\Users\sunny\Downloads\CASE STUDY\experiments\runs\retrieval-diagnostic-phase2f5-real\runner_real.py` – SHA256: 6459a802593af667e3c8ae2aab03954ed8a83f35a14ffca0afde7a93e613a40e, size: 7750 bytes, mtime: 1788426499.7438552

## 4. Invalid F3 IDs
Total invalid IDs: 209 (see CSV)

## 5. F0/F3 set consistency
F0 document set size: 209
F3 document set size: 209
F3 \- F0 (should be empty): 0

## 6. Runner‑code consistency
The `runner_real.py` implementation sorts the `f0_fused` candidate list and applies MedCPT scores; therefore every F3 ID must be a member of the F0 list. The observed mismatch indicates a breach of this contract.

## 7. Artifact modification analysis
File timestamps and hashes are recorded above. No post‑run modification timestamps were observed that would indicate later tampering (all mtime values are within the same minute window of the original execution).

## 8. Placeholder‑ID investigation
No placeholder IDs were found in repository JSON files.

## 9. Candidate‑analysis integrity
Unique (case, document) pairs in `candidate_level_analysis.jsonl`: 98

## 10. Root‑cause assessment (preliminary)
Possible explanations include:
- Post‑processing script that rewrote `f3_results.jsonl` with mismatched IDs.
- Deployment of an older runner version that emitted raw IDs before mapping to corpus identifiers.
- Accidental reuse of a stale `f3_results.jsonl` from a different experiment.
- Serialization bug that dropped or altered IDs during JSON‑L dumping.

Further investigation should compare the timestamps of `f3_results.jsonl` against the runner log and examine any scripts that touch this file.

## 11. Corrective action recommendations
- Verify the exact runner version used for this execution.
- Re‑run the pipeline with strict logging of the candidate IDs after each stage.
- Introduce a checksum validation step that confirms `f3_ranked_ids` ⊆ `f0_fused` before writing the final file.
- Until resolved, treat all downstream analyses from this run as invalid.

## 12. Scientific usability decision
Given the hard integrity failure, the current Phase 2F.5A‑REAL run **cannot** be used as evidence for any scientific claim or for designing the independent confirmation benchmark. The status is set to **INVALID / UNDER INVESTIGATION**.
