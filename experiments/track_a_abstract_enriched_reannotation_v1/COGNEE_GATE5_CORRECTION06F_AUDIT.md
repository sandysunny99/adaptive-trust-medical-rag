# COGNEE GATE 5 FINAL EVIDENCE RECONCILIATION - 06F AUDIT

## 1. Executive Summary
This audit establishes a strict protocol lock, formally separating the 21-case original frozen protocol from the 23-case amended execution matrix (which includes explicit positive control extensions authorized during Correction 06D). It strictly defines the reproducibility contract and verifies all artifacts independently.

## 2. Original Frozen Protocol
- Case count: 21 (2 POSITIVE, 19 SECURITY).
- Source: cognee_gate5_correction05.py.

## 3. Correction History
- See COGNEE_GATE5_CORRECTION06F_PROTOCOL_HISTORY.md.

## 4. Case-Matrix Ledger
- See COGNEE_GATE5_CASE_MATRIX_LEDGER.json. 

## 5. 21 vs 23 Case Reconciliation
- The original frozen protocol was **21 cases**.
- During Correction 06D, explicit user instructions mandated evaluating POS-01 through POS-04.
- This expanded the executed test suite to **23 cases**.
- 23 cases is the **amended evaluation matrix**, NOT the original frozen protocol.

## 6. Core vs Extension Cases
- **FROZEN_CORE_CASESET**: 21 historical cases.
- **EXTENSION_CASESET**: EXT-POS-03, EXT-POS-04.
- Combined execution count: 23.

## 7. Expected Outcome Sources
- Derived from PROTOCOL_MATRIX_V2 / authoritative design documents.

## 8. Runtime Accounting
- Executed unique cases: 23. Total runs: 69.

## 9. Cognee Retrieval Accounting
- 46 total Cognee retrieval cases (23 x 2 runs).

## 10. Baseline Accounting
- 23 COGNEE_OFF runs.

## 11. Positive Controls
- Evaluated as POS-01 through POS-04.

## 12. POS-02 Retrieval Contamination
- **Retrieval Result**: CONTAMINATED
- **Security Result**: BLOCK
- **Protocol Expected Result**: RELEASE (Clean), BLOCK (Contaminated).
- POS-02 remains a valid safety containment success with a retrieval failure. It is explicitly not conflated with a normal clean success.

## 13. PROV-06 Interpretation
- **Expected Outcome**: RELEASE.
- **Actual Outcome**: RELEASE.
- PROV-06 was intentionally designed to RELEASE under protocol rules. It represents an accepted deviation, not a "blocked corruption."

## 14. Integrity Evidence
- 100% of candidate modifications were correctly blocked and mapped.

## 15. Prompt Injection Evidence
- Prompt injection targets successfully intercepted.

## 16. Provenance Evidence
- Full structural provenance mapping (source, status, IDs) verified on all candidates.

## 17. Grounding Evidence
- Tracked comprehensively.

## 18. Reproducibility Contract
- Contract defined explicitly across decision logic and retrieval outputs. See COGNEE_GATE5_CORRECTION06F_REPRODUCIBILITY_CONTRACT_AUDIT.md.

## 19. Decision Reproducibility
- DECISION_EXACT_MATCH: All required security/gate decisions observed and equal.

## 20. Retrieval Reproducibility
- OBSERVED_RETRIEVAL_EXACT_MATCH: All retrieval fields defined for this experiment observed and equal.

## 21. Full Reproducibility
- FULL_EXACT_MATCH: Achieved because both decision and retrieval contracts are completely satisfied and observed natively.

## 22. RG-02 Failure
- RG-02 target chunk was retrieved, but relationship grounding was not robustly evaluated due to prototype regex limitations. 
- Reason: Prototype unsupported format.
- Status: FAILED (Gate Released when Block was expected).

## 23. Artifact Integrity
- PASSED (Zero conflicts across version checks).

## 24. Experiment Validation
- FAILED_WITH_LIMITATIONS (Due to RG-02 logic).

## 25. Gate 5
- NOT PASSED / STOPPED.

## 26. Gate 6
- NOT AUTHORIZED / STOPPED.
