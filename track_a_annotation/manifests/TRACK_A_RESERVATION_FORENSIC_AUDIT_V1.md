# TRACK_A_RESERVATION_FORENSIC_AUDIT_V1

## Registry Total
- Total entries: 80

## Batch-by-batch Counts
| Batch ID | Entries | RESERVED | COMMITTED | RELEASED | UNKNOWN |
|---|---|---|---|---|---|
| TRACK_A_A_BATCH_001 | 10 | 0 | 10 | 0 | 0 |
| TRACK_A_A_BATCH_002 | 10 | 10 | 0 | 0 | 0 |
| TRACK_A_A_BATCH_003 | 60 | 60 | 0 | 0 | 0 |

## Position-level Conflicts
- Multiple-batch assignments: 0
None

## Orphan Entries
- Orphan reservations: 0
None

## Artifact/Registry Mismatches
- Mismatches: 0
None

## Batch Status
- Batch 001 status: 10 COMMITTED, OK
- Batch 002 status: 10 RESERVED, OK
- Batch 003 status: 60 RESERVED, OK

## Dataset Reconciliation
- Active reservation total: 70
- Annotated total: 11
- Available total: 449

## Exact Explanation of the 80 Count
Registry total entries = 80

10 Batch 001 COMMITTED
10 Batch 002 RESERVED
60 Batch 003 RESERVED

Active reservations = 70

Therefore available unreserved unannotated:
530 - 11 - 70 = 449


## Additional Batches Check
- Later batches found: None
