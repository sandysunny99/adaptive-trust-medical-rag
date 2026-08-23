# Dataset Integrity & Segregation Audit

## Dataset Splits & Segregation Rules

| Split | Case Count | Purpose | Segregation Rule | Verification Status |
|-------|------------|---------|------------------|---------------------|
| **Smoke** | 20 | Rapid CI & local integration testing | Generated dynamically | PASSED (PHI-free) |
| **Dev** | 100 | Component tuning & prompt iteration | Fixture: `dev_dataset_v1.jsonl` | PASSED (PHI-free) |
| **Val** | 200 | Hyperparameter & threshold validation | Fixture: `val_dataset_v1.jsonl` | PASSED (PHI-free) |
| **Test** | 500+ | Frozen benchmarking & final paper evaluation | **STRICTLY FROZEN** (`allow_test=True` required) | PASSED (Zero leakage) |

## PHI & Security Verification
- All test fixtures pass zero-PHI validation routines (`verify_no_phi()`).
- Zero patient names, SSNs, phone numbers, or MRNs present in dataset fixtures.
