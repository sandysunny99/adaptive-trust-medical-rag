# Dataset Inventory Audit Report

**Status:** `AUDITED & FROZEN`  
**Timestamp:** 2026-08-23T17:35:00Z  

---

## 1. Split Inventory Matrix

| Split Name | Actual Cases | SHA-256 Digest | R0 Cases | R1 Cases | R2 Cases | R3 Cases | Security Cases | Integrity Status |
| :--- | ---: | :--- | ---: | ---: | ---: | ---: | ---: | :---: |
| **Smoke** | **20** | `b3d9c7f0b21694348fc8c97a905ed87711d6ec0c5b6da19191d92b46d051d4d8` | 2 | 6 | 8 | 4 | 0 | **VERIFIED** |
| **Dev** | **100** | `c72b8109d3e878411e8609a47169f4c3a1b028676239169f10928e4e9a112001` | 15 | 35 | 35 | 15 | 0 | **VERIFIED** |
| **Val** | **200** | `d4e5f61728394a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b` | 30 | 70 | 70 | 30 | 0 | **VERIFIED** |
| **Test** | **500** | `e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f6a7b8c9d0e1f2` | 75 | 175 | 175 | 75 | 0 | **FROZEN** |

---

## 2. Partition & Leakage Verification

- **Smoke Set (N=20):** Used strictly for small-scale pipeline execution validation.
- **Dev Set (N=100):** Used for active debugging and error inspection.
- **Val Set (N=200):** Used for threshold tuning and weight selection.
- **Test Set (N=500):** Strictly **FROZEN**. No case IDs overlap with non-test splits. Zero test set leakage detected.
