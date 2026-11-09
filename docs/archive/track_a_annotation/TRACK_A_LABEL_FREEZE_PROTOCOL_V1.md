# TRACK_A_LABEL_FREEZE_PROTOCOL_V1

## Overview
This protocol defines the strict requirements and state transitions required to move the human annotation workspace from an active state into an immutable `FROZEN` state.

## 1. Pre-requisites for Freeze
A freeze is only permitted when ALL of the following criteria are met:
- [ ] 100% of the 530 required positions have an `annotation_status` of `ANNOTATED` or `QA_RESOLVED`. No positions may remain `UNANNOTATED`, `IN_PROGRESS`, or `QA_FLAGGED`.
- [ ] Inter-Annotator Agreement (IAA) overlap (50 positions) is complete, independently recorded, and metrics have been calculated.
- [ ] The automated QA script (`scripts/track_a_annotation_qa.py`) executes with exactly **0 blocking errors**.
- [ ] The schema version is confirmed and fixed (V2.0.0).
- [ ] Dataset identity hash matches expectations (`3b1355a08c...`).
- [ ] Annotator provenance (IDs, rationales, spans) is completely preserved.
- [ ] Absolutely NO automatic/LLM-generated relevance labels exist in the dataset.
- [ ] All protocol exceptions (e.g. missing abstracts forced to `INSUFFICIENT_INFORMATION`) are formally documented.

## 2. Freeze Execution
Once pre-requisites are verified:
1. All records in the workspace are marked with `annotation_status = "FROZEN"`.
2. A final JSONL export is generated.
3. The dataset is canonicalized (keys sorted, timestamps excluded/normalized).
4. The canonical SHA-256 hash is computed and logged.
5. The global state `TRACK_A_LABELS_FROZEN` is formally declared.

## 3. Post-Freeze Mutability Rules
After the freeze declaration, the labels become **immutable**.

Any corrections required after the freeze must follow a formal amendment procedure:
- A new version identifier is established (e.g., V2.1.0).
- A new dataset hash is generated.
- A documented reason for amendment is required.
- Affected `position_id`s, previous values, and new values must be logged.
- An explicit approval/audit record must be appended.

**SILENT EDITS TO FROZEN LABELS ARE STRICTLY PROHIBITED.**
