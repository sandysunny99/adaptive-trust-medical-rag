# TRACK_A_ARTIFACT_INVENTORY_V1

## Executive Summary
This document inventories the existing frozen and mutable Track A annotation-related artifacts found in the repository prior to generating the human annotation workspace.

## Inventory

| Artifact | Path | Purpose | Hash | Status | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Track A Human Annotation Dataset (V1)** | `TRACK_A_HUMAN_ANNOTATION_DATASET_V1.jsonl` | The core dataset containing 530 evaluation positions intended for human relevance grading. | `3b1355a08c87ef2b32e1a0c78dbe8211e042d6dea4339619867d73b652cb56f4` | FROZEN | 1.35MB JSONL file. Base for human labeling. |
| **Track A Annotation Schema (V1)** | `TRACK_A_ANNOTATION_SCHEMA_V1.json` | JSON Schema for validation of relevance, rationale, and label metadata. | `ad16135192eec128052056d4320161a46fe80005ad9560c64d3b8863199f0586` | FROZEN | Will be audited and extended in V2 if lacking required QA fields. |
| **Track A Human Annotation Guide (V1)** | `TRACK_A_HUMAN_ANNOTATION_GUIDE_V1.md` | Human instructions for relevance classification. | `13a91dbce55acb52da314975b7c3d093f42ac2680546952f4d1d924d4295f010` | FROZEN | Will be migrated to V2 to ensure explicit handling of missing abstracts and bounds. |
| **Track A Metric Definitions (V1)** | `TRACK_A_METRIC_DEFINITIONS_V1.md` | Definition of the formal metrics calculated after labels are frozen (e.g. nDCG, MRR). | `a744b181a94e71eaf76bd7d39447cc6a973ca93fefc2ad7de16aa91256b8063a` | FROZEN | Establishes quadratic weighted Cohen's Kappa. |
| **Track A Evaluation Protocol (V1)** | `TRACK_A_EVALUATION_PROTOCOL_V1.md` | General protocol defining the overarching Track A process. | `cc39185e05211f6654999e0b44ccdb9856eee65f6c3abc28088395cce3484f63` | FROZEN | Locks evaluation methods. |
| **Track A Reproducibility Contract (V1)** | `TRACK_A_REPRODUCIBILITY_CONTRACT_V1.md` | The contract that must be adhered to for result replication. | `8354285e7b3ac2353a33006fe028c9e431accb8725623579fd13ac7279fc6967` | FROZEN | Will be incremented to V2 for the label freeze constraints. |
| **Track A Inter-Annotator Agreement (V1)** | `TRACK_A_INTERANNOTATOR_AGREEMENT_V1.md` | Prior agreement expectations. | `9896e2eab027f61495f0504868aee2a66a01de7b94c29da9e5d13fe7a6e4ca8c` | FROZEN | To be replaced/augmented by explicit protocol. |
| **Track A Dataset Audit (V1)** | `TRACK_A_DATASET_AUDIT_V1.json` | Prior audit tracking the dataset composition. | `93f19b765ec2bc07f518c4b711c3d113bdb99ebaeedbf9cb3951300447e0ff1f` | FROZEN | Historical structural audit. |
| **Track A Annotation QA (V1)** | `TRACK_A_ANNOTATION_QA_V1.json` | Previous QA output run. | `02a62eee780ec906b92c08419dd172994f7d0e609d86bb0d1857f61d7dbfcf20` | MUTABLE | Will be overwritten or version-bumped by new QA outputs. |
| **Track A Annotation Freeze (V1)** | `TRACK_A_ANNOTATION_FREEZE_V1.md` | Historical freeze declaration. | `28f1b778d28969ff0f96fb72a2b56dda0605659bceee78a4de1a484264e122f7` | FROZEN | Will be strictly enforced. |
| **Abstract Enriched Source Snapshot** | `experiments/track_a_abstract_enriched_reannotation_v1/TRACK_A_ABSTRACT_ENRICHED_SOURCE_SNAPSHOT.jsonl` | Sourced dataset representing chunks + retrieved metadata abstracts. | `7675691b41e59e316bbbbde02a7d040b81f9f30c072e0a17f47fccbfb2a097ad` | FROZEN | Contains the explicit evidence to be labeled. |
