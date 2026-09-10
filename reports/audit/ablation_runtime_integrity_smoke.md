# Ablation Runtime Integrity Audit (Smoke)

**Status:** `FAIL`
**Timestamp:** 2026-09-10T20:45:45.840120+00:00

---

## 1. Runtime Component Execution Matrix

| Variant | Total | Dense | BM25 | Graph | Trust | Verifier | Status |
| :--- | ---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **A** | 20 | NO | NO | NO | NO | NO | **PASS** |
| **B** | 20 | YES | NO | NO | NO | NO | **PASS** |
| **C** | 0 | YES | YES | NO | NO | NO | **PASS** |
| **D** | 0 | YES | YES | YES | NO | NO | **PASS** |
| **E** | 0 | YES | YES | YES | YES | NO | **PASS** |
| **F** | 0 | YES | YES | YES | YES | YES | **PASS** |
