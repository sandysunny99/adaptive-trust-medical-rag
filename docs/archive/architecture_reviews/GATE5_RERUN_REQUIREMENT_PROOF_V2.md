# GATE 5 RERUN REQUIREMENT PROOF V2

**Date:** 2026-10-03  

This document separates code differences from numerical differences, and semantic changes from methodological requirements, to explicitly prove when an official rerun is needed.

## 1. Trust Policy

**Option A (Imputation)**
- **Numerical Difference:** YES. (0.0 becomes >0.0).
- **Semantic Difference:** YES. (Missing factor is now a measured signal).
- **Methodological Difference:** YES. (The trust formula logic changes).
- **Historical Reproducibility:** BROKEN.
- **Official Rerun Required:** **YES.** The Cognee benchmark cannot be compared against the old baseline because the eligibility gate behaves differently.

**Option B (Renormalization)**
- **Numerical Difference:** YES. (Remaining 7 factors scale up).
- **Semantic Difference:** YES. (Transitions to a 7-factor model).
- **Methodological Difference:** YES.
- **Historical Reproducibility:** BROKEN.
- **Official Rerun Required:** **YES.**

**Option C (Keep Missing=Zero)**
- **Numerical Difference:** NO.
- **Semantic Difference:** NO.
- **Methodological Difference:** NO. (Preserves current implementation).
- **Historical Reproducibility:** PRESERVED.
- **Official Rerun Required:** **NO.**

## 2. Anti-Injection Policy

**Option A (Keep Constant 1.0)**
- **Numerical Difference:** NO. (Historical was `1.0 - 0.0 = 1.0`, Current is `1.0`).
- **Semantic Difference:** YES. (Historical treated it as measurement; current explicitly treats it as a constant placeholder).
- **Methodological Difference:** MINOR. (Acknowledges it as a placeholder).
- **Historical Reproducibility:** PRESERVED (Numerically identical).
- **Official Rerun Required:** **NO.** A semantic classification change without a numerical shift does not invalidate the CSV/JSON baseline records.

**Option B (Remove / Hard Gate Only)**
- **Numerical Difference:** YES. (Denominator drops by 0.01 to 0.10; remaining weights shift up).
- **Semantic Difference:** YES. (Removes from continuous trust).
- **Methodological Difference:** YES.
- **Historical Reproducibility:** BROKEN.
- **Official Rerun Required:** **YES.**

**Option C (Continuous Measurement)**
- **Numerical Difference:** YES.
- **Semantic Difference:** YES.
- **Methodological Difference:** YES.
- **Historical Reproducibility:** BROKEN.
- **Official Rerun Required:** **YES.**
