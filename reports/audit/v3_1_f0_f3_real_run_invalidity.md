# Real‑run Result Invalidity Report

**STATUS:** INVALID / REQUIRES FORENSIC RECONCILIATION

**REASON:** F3 result artifacts contain document IDs that are absent from the frozen 248‑document corpus, violating the runner architecture that should only rerank F0 candidates.

- Number of invalid F3 document IDs: 209
- All invalid IDs are listed in `v3_1_invalid_f3_id_forensics.csv`.

**ACTION:** Preserve the original run directory and copy it to `retrieval-diagnostic-phase2f5-real-invalid/` for forensic analysis. No further scientific interpretation should be drawn from these results until reconciliation is completed.
