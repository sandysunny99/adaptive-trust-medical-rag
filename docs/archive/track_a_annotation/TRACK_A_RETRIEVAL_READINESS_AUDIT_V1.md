# TRACK_A_RETRIEVAL_READINESS_AUDIT_V1

## Overview
This audit establishes the readiness of the Track A Retrieval Benchmark for human annotation and the subsequent calculation of standard retrieval metrics (Recall, Precision, nDCG, MRR). No final retrieval executions or metric calculations were performed during this audit; the focus was purely on protocol and dataset integrity.

## Dataset Audit Results
The `TRACK_A_ABSTRACT_ENRICHED_SOURCE_SNAPSHOT.jsonl` dataset was parsed and audited:
- **Total Evaluation Positions:** 530
- **Unique Queries:** 9 (distributed across the 530 positions)
- **Duplicate Chunks/Documents:** 0 within positions.
- **Missing Abstracts:** 8 positions (`pos-86bb114a`, `pos-a9e7c46c`, `pos-b162a84a`, `pos-4c8cc2be`, `pos-3d27c5b0`, `pos-10aae2c8`, `pos-aa15aacd`, `pos-bc7bb827`).
- **Adjudication Required:** The 8 positions lacking abstracts are flagged for explicit human adjudication according to the schema (defaulting to `INSUFFICIENT_INFORMATION` unless the title independently resolves the query).
- **Missing Provenance:** None observed.

*Note: The 8 missing-abstract positions are not silently deleted. They are preserved and handled deterministically via the annotation schema to avoid artificially inflating metrics.*

## Relevance Definitions & Annotation Schema
A graded relevance schema was defined to support nDCG@K calculations:
- `RELEVANT` (2): Explicit pharmacological top-tier match.
- `PARTIALLY_RELEVANT` (1): Related entities but missing the specific relationship/outcome.
- `IRRELEVANT` (0) / `INSUFFICIENT_INFORMATION` (0): No topical match or insufficient data.
- `AMBIGUOUS`: Requires senior adjudication.

## Metric Design
- **Recall/Precision/MRR**: Computed using binarized labels (only Grade 2 counts as positive).
- **nDCG@K**: Utilizes the full graded schema.
- Queries with exactly 0 known relevant chunks corpus-wide will be excluded from the macro-average Recall calculation.

## Configuration Standardization
The baseline configuration (`S-PubMedBERT-MS-MARCO`, RRF k=60, Top-K=10) and the Cognee configuration are locked. Both systems interrogate identical evidence corpora without synthetic target injection.

## Final Decision
**TRACK_A_READY_FOR_HUMAN_ANNOTATION**

The dataset, annotation schema, metric definitions, and reproducibility contracts are fully established and sound. The benchmark is completely separated from Gate 5 security logic and is ready to generate scientifically defensible retrieval relevance metrics.
