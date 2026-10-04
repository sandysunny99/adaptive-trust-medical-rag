# TRACK A BATCH 005 SELECTION PROVENANCE V1

| Window | Selection Script | Input Source | Selection Rule | IDs Created | Registry Reservation | Status |
|---|---|---|---|---|---|---|
| 01-05 | scratch/commit_prep_window*.py | TRACK_A_ANNOTATOR_A.jsonl | First 10 unannotated positions | 10 per window | NONE / Bypassed | INVALID |

Root Cause: Ad-hoc scripts read directly from the master dataset, pulling the next unannotated records and manually tagging them as 'Batch 005', bypassing the authoritative TRACK_A_RESERVED_POSITIONS.json manifest entirely. Batch 005 does not exist formally.
