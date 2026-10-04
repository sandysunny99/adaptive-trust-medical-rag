# TRACK_A_ANNOTATION_REPRODUCIBILITY_V2

## Purpose
This contract ensures that any researcher can accurately reconstruct the exact dataset, schema, and environmental conditions under which the human relevance labels were generated.

## Verification Vectors

| Component | Value/Protocol |
| :--- | :--- |
| **Dataset Identity** | `TRACK_A_HUMAN_ANNOTATION_DATASET_V1.jsonl` |
| **Dataset Hash (SHA-256)** | `3b1355a08c87ef2b32e1a0c78dbe8211e042d6dea4339619867d73b652cb56f4` |
| **Annotation Workspace** | `track_a_annotation/annotation_workspace/TRACK_A_WORKSPACE_V1.jsonl` |
| **Schema Version** | `2.0.0` (`TRACK_A_ANNOTATION_SCHEMA_V2.json`) |
| **IAA Overlap Subset** | `TRACK_A_IAA_OVERLAP_MANIFEST_V1.json` (Seed = 42, Size = 50) |

## Export and Canonicalization Rules
1. All annotations must be exported as JSONL.
2. Keys within each JSON object must be sorted alphabetically before hashing.
3. Volatile timestamps (`timestamp`) must be explicitly excluded from canonical content hashes used for reproducibility checksums, or canonicalized to a fixed string (e.g. `<TIMESTAMP>`).

## Freeze Procedure Summary
Annotations may only enter the `FROZEN` state when 100% of the positions have a valid QA pass, IAA overlap is verified, and the annotator provenance is completely maintained. Once frozen, the labels become immutable. 

**Any structural or labeling changes made post-freeze require a new version identifier and a formal amendment document.**
