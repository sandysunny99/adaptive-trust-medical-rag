# Phase 2F.3 Candidate-Based Validation Specification

## 1. Candidate Generation
Candidates are surfaced using high-recall, multi-strategy methods (e.g., BM25, dense vector, entity graphs).

## 2. False-Negative Screening Procedure
For each case:
1. Define `unsurfaced_documents = frozen_corpus - surfaced_candidates`.
2. Select exactly 5% of the unsurfaced documents using a reproducible random seed (seed=42).
3. Record `case_id`, `population_size`, `sample_size`, `sampling_seed`, `sampled_document_ids`.
4. Run automated secondary screening to yield `POTENTIALLY_RELEVANT`, `UNCERTAIN`, or `PROBABLY_IRRELEVANT`. (No final human labels).
5. Escalate every `POTENTIALLY_RELEVANT` or `UNCERTAIN` result to the human reviewer.
6. The human reviewer independently adjudicates every escalated document (`DIRECT_SUPPORT`, `PARTIAL_SUPPORT`, `NOT_RELEVANT`, `NO_EVIDENCE`).

## 3. Case Closure
A case is formally `CASE_PROTOCOL_COMPLETE` only when:
A. All surfaced candidates have human decisions.
B. The 5% secondary screening has been executed with reproducible sampling metadata.
C. Every `POTENTIALLY_RELEVANT` or `UNCERTAIN` result has been reviewed by the human.
D. The reviewer confirms `NEW_EVIDENCE = NONE IDENTIFIED`.

## 4. Ground Truth Limitations
The un-sampled 95% remainder remains explicitly `UNSURFACED_REMAINDER` / `NOT_INDIVIDUALLY_HUMAN_REVIEWED` and cannot be bulk-labeled as `NOT_RELEVANT`.
