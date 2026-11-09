# TRACK_A_ANNOTATOR_CHECKLIST_V1

## Pre-Session Verification
At the beginning of each annotation session, confirm the following:
- [ ] Confirm your `annotator_id`.
- [ ] Confirm `schema_version` is `2.0.0`.
- [ ] Confirm `dataset_version` is `TRACK_A_HUMAN_ANNOTATION_DATASET_V1`.
- [ ] Confirm you are using `TRACK_A_HUMAN_ANNOTATION_GUIDE_V2`.
- [ ] Confirm no automated labels are being imported or substituted.
- [ ] Confirm the workspace is not modifying frozen source data (abstracts, IDs, metadata).

## Per-Position Workflow
For each position:
1. [ ] Read `query_text`.
2. [ ] Read `retrieved_evidence` (or acknowledge if `abstract_available` is false).
3. [ ] Judge relevance according to the versioned protocol.
4. [ ] Assign the permitted relevance grade/label.
5. [ ] Record rationale if required (especially for ambiguous or partially relevant cases).
6. [ ] Record exact `evidence_span` if required.
7. [ ] Save `timestamp`.
8. [ ] Mark `annotation_status` as `ANNOTATED` (or `QA_FLAGGED` if issues are suspected).

## Post-Session Actions
At session end:
- [ ] Run QA validator script (`scripts/track_a_annotation_qa.py`).
- [ ] Export a snapshot to `track_a_annotation/snapshots/`.
- [ ] Record number of positions completed in the session log.
- [ ] Record number of positions remaining.
- [ ] **Do NOT freeze partial work unless the protocol permits it.**
