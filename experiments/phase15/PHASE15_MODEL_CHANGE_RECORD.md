# Phase 15 Model Change Record

**Date:** 2026-09-08
**Type:** Pre-Execution Configuration Correction

## 1. Reason for Change
The originally frozen model identifier (`gemini-1.5-pro`) was an invalid/retired generation model (shut down September 29, 2025). The intermediate identifier (`gemini-3.1-pro`) was incorrectly labeled as "stable production" when official Google documentation explicitly designates it as a preview model with the specific API identifier `gemini-3.1-pro-preview`. 

## 2. Model Replacement

| Attribute | History | Final Exact API Identifier |
|-----------|---------|----------------------------|
| **Previous Invalid Identifier** | `gemini-1.5-pro` | |
| **Intermediate Incorrect Identifier** | `gemini-3.1-pro` | |
| **Final Exact API Identifier** | | `gemini-3.1-pro-preview` |
| **Provider** | | Google Gemini API |
| **Model Lifecycle Status** | | PREVIEW |

**Availability Verification Evidence:**
`gemini-3.1-pro-preview` supports the required 1M-token context window, deterministic sampling parameters (temperature 0.0), structured outputs, and function calling required by the Phase 14 architecture. It is officially documented and available for experimental workloads.

## 3. Protocol and Dataset Impact
- **Expected Behavioral Differences:** As a preview model, the evaluation measures the frozen behavior of this specific configuration and should not be interpreted as a general evaluation of all Gemini models or of a permanently stable model release. 
- **Protocol Modification:** `PHASE15_PROTOCOL.md` was updated with explicit limitations regarding preview status and API determinism.
- **Dataset Modification:** The dataset (`phase15_cases.jsonl`) remains **byte-identical**. No cases were added, removed, or regenerated. N=200 remains unchanged.
- **Statistical Plan / Failure Taxonomy / Design Boundaries:** Unchanged.

## 4. Exact Files Changed
1. `experiments/phase15/PHASE15_CONFIGURATION_FREEZE.json`
2. `experiments/phase15/PHASE15_PROTOCOL.md`
3. `experiments/phase15/PHASE15_FREEZE_MANIFEST.json`
4. `experiments/phase15/PHASE15_FINAL_FREEZE_STATUS.md`
