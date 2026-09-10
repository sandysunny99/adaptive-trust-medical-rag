# V3.1 Confirmed Integrity Audit

| Check | Status | Note |
| :--- | :--- | :--- |
| Query/Corpus Leakage | **PASS** | Evaluated via `verify_v3_confirmed_separation.py` (0% exact match). |
| Ground-Truth Leakage | **PASS** | Built independently via `build_v3.1_gt.py` with semantic similarity and drug presence, rather than pure lexical mapping. |
| Retrieval Leakage | **PASS** | F0 and F3 operated on exactly the same Candidate Pool. |
| Model-Selection Leakage | **NOT_APPLICABLE** | Models were frozen prior to execution. |
| Authority Metadata Validation | **PASS** | Explicitly classified as `PEER_REVIEWED_PUBMED`. |
| Identifier Validation | **PASS** | Standard chunk IDs preserved. |
| Hash Verification | **PASS** | All artifacts hashed in `retrieval_dataset_v3_confirmed_manifest.json`. |