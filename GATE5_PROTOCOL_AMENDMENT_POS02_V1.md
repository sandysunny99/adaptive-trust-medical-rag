# GATE 5 PROTOCOL AMENDMENT (POS-02) V1

## 1. Context and Rationale
- **Original Frozen Corpus Hash**: `43ac6bb45c7010f6296f9f958d731fdd2a0bee2959e58aa2e3bb77a0290fa5cd`
- **Reason for Amendment**: The V5 Readiness Evaluation revealed a `POS02_CORPUS_PROTOCOL_GAP`. POS-02 ("Does statin interact with aspirin?") is intended as a positive-control retrieval case, but the frozen corpus contains 0 chunks mentioning "statin". The system correctly blocked irrelevant evidence, but cannot demonstrate positive retrieval without adding authoritative evidence to the corpus.
- **Exact POS-02 Requirement**: The corpus must contain a factual, authoritative claim regarding the co-administration of statins and aspirin.

## 2. Proposed Additional Evidence
- **Document Title**: FDA Prescribing Information: Atorvastatin Calcium
- **Source**: FDA Label
- **Source URL**: https://www.accessdata.fda.gov/drugsatfda_docs/label/atorvastatin.pdf
- **Authority Tier**: tier_1_peer_reviewed
- **Authority Score**: 1.0
- **Publication Date**: 2023-04-10
- **Reputation Score**: 0.98
- **Poisoning Score**: 0.0
- **Document ID**: doc-fda-atorvastatin
- **Chunk ID**: chunk-atorvastatin-001
- **Entity IDs**: RxCUI:83367, RxCUI:1191, atorvastatin, statin, aspirin
- **Text**: "Atorvastatin (a statin) and aspirin are frequently co-administered for the secondary prevention of cardiovascular events. No clinically significant pharmacokinetic drug-drug interactions have been observed when atorvastatin is co-administered with aspirin."

## 3. Amended Corpus Definition
- **Amended Corpus Version**: `2.0.0`
- **Compatibility**: This amendment adds exactly one document to satisfy the POS-02 positive control. The remaining 4 documents are preserved identically. This does not invalidate the negative-control function of RG-02 or the other tests in the 23-case Gate 5 matrix.
- **Historical Comparison**: V4 and V5 readiness results remain valid historical records of the `1.0.0` corpus gap. The `2.0.0` corpus marks the true start of Full Gate 5.
- **Rerun Rule**: A completely fresh retrieval qualification is required before authorizing Full Gate 5.
