# TRACK A BATCH 005 WINDOW 05 REPAIR AUDIT V1

1. Incident summary: The staged Window 05 packet contained IDs that conflict with the authoritative registry.
2. Original staged IDs: ['pos-cbaac358', 'pos-6b51aa62', 'pos-41410b52', 'pos-47d7ebb4', 'pos-a835aaac', 'pos-5b711aba', 'pos-eb331f6c', 'pos-e8bcb783', 'pos-b043af88', 'pos-19c49db1']
3. Registry ownership: ['pos-cbaac358', 'pos-6b51aa62', 'pos-41410b52', 'pos-47d7ebb4', 'pos-a835aaac', 'pos-5b711aba'] belong to TRACK_A_A_BATCH_003.
4. Missing registry IDs: ['pos-eb331f6c', 'pos-e8bcb783', 'pos-b043af88', 'pos-19c49db1'] are missing from the registry.
5. Batch provenance: Batch 005 was never formally reserved.
6. Root cause: Bypassed registry validation in ad-hoc staging scripts.
7. Selection-provenance evidence: Scripts extracted next unannotated records directly from master.
8. Master dataset status: Unchanged (75 annotated).
9. Registry before hash: 1406125db5056e58012a78584a8dde115f9d41149475ba2735bf99cbb597fc6d
10. Registry after hash: 1406125db5056e58012a78584a8dde115f9d41149475ba2735bf99cbb597fc6d
11. Modified files: NONE (only new forensic artifacts created).
12. Canonical next eligible positions: ['pos-cbaac358', 'pos-6b51aa62', 'pos-41410b52', 'pos-47d7ebb4', 'pos-a835aaac', 'pos-5b711aba']
13. New Window 05 required: YES
14. New human annotation required: YES
15. Recommended execution path: PATH 1 (Create new clean Batch 005 reservation if Batch 003 is depleted, or process the remaining Batch 003 positions canonically).
