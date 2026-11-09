# TRACK_A_REPRODUCIBILITY_CONTRACT_V1

## 1. Retrieval Experiment Identity
To ensure strict scientific reproducibility, the final Track A execution must be locked to the following cryptographic and versioned identities:

- **Corpus Hash**: `adae7e315cdc39a2d00ec58a05516b685251af51207a18ab3368ee0d9022a847` (V2.0.0 Amended Manifest)
- **Query-Set Snapshot**: `TRACK_A_ABSTRACT_ENRICHED_SOURCE_SNAPSHOT.jsonl`
- **Annotation-Schema Version**: V1.0.0 (`TRACK_A_ANNOTATION_SCHEMA_V1.json`)
- **Retrieval Model**: `S-PubMedBERT-MS-MARCO` 
- **Retrieval Engine Configurations**: Defined in `TRACK_A_EVALUATION_PROTOCOL_V1.md`
- **Top-K Limit**: 10
- **Software Environment**: Defined via `uv.lock` dependency tree.

## 2. Independence of Repeated Runs
When verifying the stability and determinism of the retrieval engines, repeated runs must be evaluated entirely independently. The orchestrator must not share state or cache between iterations.

The following must be compared for exact match across repetitions:
- **Retrieved Candidate IDs**: The exact sequence of chunks retrieved.
- **Candidate Ranks**: The integer position of the chunks in the top-K list.
- **Similarity/RRF Scores**: The raw float scores dictating the rank order.
- **Final Ordering**: The absolute ordering presented to the annotation mapping layer.

Any stochastic variation in retrieval results (e.g., tie-breaking differences) must be explicitly quantified and reported.
