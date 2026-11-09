# GATE5_FULL_EXECUTION_AUDIT

## Full Gate 5 Matrix Execution Record

### Scope
- **Matrix:** 21 Frozen Core cases + 2 Controls = 23 Cases
- **Engines:** Baseline (HybridRetrievalEngine, S-PubMedBert-MS-MARCO) & Live CogneeRetrievalAdapter
- **Runs:** 2 runs per case per engine to ensure deterministic behavior.
- **Corpus:** 2.0.0 (FDA labels updated to `tier_1_regulatory`, synthetic pos-02 purged, real FDA Atorvastatin label added).
- **Corpus Hash:** `adae7e315cdc39a2d00ec58a05516b685251af51207a18ab3368ee0d9022a847`

### Execution Highlights
- **Semantic Mapping Intact:** The system correctly identifies positive vs. bounded negative polarities.
- **POS-02 Verification:** The query "Does statin interact with aspirin?" consistently returns the bounded negative finding from `doc-fda-atorvastatin` (`chunk-atorvastatin-001`). The trace explicitly registers:
  - `RETRIEVAL_POSITIVE_RETRIEVED`
  - `INTERACTS_WITH` (NEGATED, CLINICALLY_SIGNIFICANT)
  - `BOUNDED_NEGATIVE`
- **RG-02 Verification:** The query "Statin is a drug. Cyanide is a poison." correctly registers `NO_RELEVANT_RELATION` and is blocked.
- **Reproducibility:** Confirmed absolute reproducibility of the security states and retrieval ranks across both runs.

### Conclusion
The entire 23-case matrix completed in perfect conformance with the protocol. All claims safety and integrity checks passed.
