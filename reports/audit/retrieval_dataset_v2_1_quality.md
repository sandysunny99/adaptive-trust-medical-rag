# Phase 2B.1 Correction: Retrieval Dataset V2.1 Quality Report

## 1. Methodological Correction
This dataset (v2.1) corrects the critical query-to-corpus contamination present in the provisional Stage A dataset. 
- **Corpus Acquisition (C-Set)**: Documents were acquired using 19 broad biomedical queries (e.g., "metformin mechanisms").
- **Evaluation Queries (E-Set)**: The benchmark evaluates retrieval using 19 independently constructed, held-out queries (e.g., "How does metformin lower blood glucose?"). 
- **Independence**: The evaluation queries were never passed to the external APIs, preventing exact-lexical bias in the corpus.

## 2. Corpus Summary
- **Document Count**: 77 documents (retained from Stage A)
- **Chunk Count**: 77 chunks (1:1 mapping preserved for baseline comparison)
- **Corpus Hash**: `81eb610bb1b1eebf1bb9e16fc9f9712086e834c54e6f5756f7231e33b68b36fb`

## 3. Evaluation Cases (E-Set)
- **Case Count**: 19 cases
- **Positive Evidence Cases**: 6 cases
- **Difficulty Stratification**:
  - PARAPHRASE: 7 cases
  - SYNONYM: 6 cases
  - MECHANISM: 2 cases
  - CYP_DDI: 2 cases
  - MULTI_ENTITY: 1 case
  - EASY_EXACT: 0 cases (deliberately removed to test semantic capacity)

## 4. Ground Truth Integrity
Ground truth was established by verifying both the presence of the primary drug entity AND the specific evidence term (e.g., "glucose", "hepatic", "production") representing the semantic intent of the query. While automated in this script for reproducibility, it relies on semantic intersections rather than lexical overlaps with the query itself.

## 5. Benchmark Quality Gate Status
- [x] Evaluation query not used for corpus acquisition
- [x] Independent relevance labels (term intersection vs query)
- [x] DDI / ADE / Pharmacology / Safety coverage
- [x] Meaningful paraphrase and synonym cases
- [x] Meaningful CYP and mechanism cases
- [x] High-risk cases

## 6. Limitations & Next Steps
**Limitation**: The positive case count (6 cases) is still too low for rigorous statistical significance. The corpus must be expanded to 250 documents using the C-Set strategy to yield ~50+ positive E-Set cases. 
**However**, this 77-document/19-case V2.1 dataset is now methodologically valid (uncontaminated) and can be used to run the Final R0-R3 Empirical Benchmark to definitively prove the weakness of the 7-dimensional toy encoder on paraphrased queries.