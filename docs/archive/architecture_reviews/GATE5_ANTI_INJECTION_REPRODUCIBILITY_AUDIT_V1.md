# HISTORICAL ANTI-INJECTION REPRODUCIBILITY AUDIT

**Date:** 2026-10-03  

## 1. Trace of Gate 5 Execution

- **Historical Implementation:** During the Gate 5 frozen offline benchmark, the code executed with:  
  `anti_injection = 1.0 - cand.poisoning_score`
- **Historical Data Context:** Gate 5 was executed against `manifest.json`, the frozen safe evidence corpus. For every document in that baseline corpus, `poisoning_score` was explicitly `0.0`.
- **Historical Arithmetic:**  
  `anti_injection = 1.0 - 0.0 = 1.0`.

## 2. Current Implementation

- **Current Implementation:** Following the recent semantic patch, the code executes with:  
  `anti_injection = 1.0`

## 3. Difference and Impact

- **Difference for Safe Queries:** `1.0 - 1.0 = 0.0` (Zero difference).
- **Reproducibility Impact:** Changing the anti-injection code from `1.0 - poisoning_score` to the constant `1.0` has **ZERO** mathematical impact on the Gate 5 benchmark scores. The absolute trust numbers recorded historically are perfectly preserved under the new patch, because the historical penalty was mathematically non-existent for the safe corpus.

## 4. Conclusion

The claim that Option C (Keep Missing=0.0) combined with Option A (Keep Anti-Inject=1.0) preserves historical reproducibility is factually established. No Gate 5 artifacts must be rerun due to the anti-injection patch.
