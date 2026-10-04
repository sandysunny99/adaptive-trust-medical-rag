# TARGETED RG-02 GATE 5 NATIVE RETRIEVAL AUDIT TRAIL

## Objective
Observe actual native retrieval behavior for RG-02 and control cases in Baseline (Hybrid) and Cognee, without artificial vocabularies, mock normalizers, or expected-document filtering.

## Findings
- Cognee path was actually invoked (no Hybrid fallback).
- No expected_doc_id filtering occurred.
- Real DrugNormalizer was used.

## RG-02 Native Retrieval Observation
RG02_RETRIEVAL_STATUS = NATIVELY_RETRIEVED
The system natively retrieved `doc_rg02`.
