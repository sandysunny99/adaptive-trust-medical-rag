# TRACK_A_SCHEMA_AUDIT_V2

## Audit Objective
Verify the existing annotation schema (`TRACK_A_ANNOTATION_SCHEMA_V1.json`) to ensure it possesses all required metadata structures necessary for a controlled human annotation trace.

## V1 Schema Analysis
The existing V1 schema focuses entirely on class label definitions (`RELEVANT`, `PARTIALLY_RELEVANT`, `IRRELEVANT`, `INSUFFICIENT_INFORMATION`, `AMBIGUOUS`) and their integer grading.

**Missing fields required for rigorous human annotation control:**
- `annotator_id`
- `rationale`
- `evidence_span`
- `timestamp`
- `schema_version` (was only present at root, not structurally enforced per record)
- `position_id` / `query_id`
- `annotation_status`

## Versioned Extension
A new schema, `TRACK_A_ANNOTATION_SCHEMA_V2.json`, has been generated. It retains the identical ordinal and categorical label definitions from V1 to avoid semantic drift, while structurally enforcing the tracking properties necessary for reproducible research.

### Added Structural Enforcements
1. `fields_required`: Defines the minimum object keys for a valid annotation record.
2. `annotation_states`: Implements the formal lifecycle states (`UNANNOTATED`, `IN_PROGRESS`, `ANNOTATED`, `QA_FLAGGED`, `QA_RESOLVED`, `FROZEN`).

## Migration Strategy
No existing annotations will be silently migrated because no human labels exist yet. The new workspace initialized for annotators will use the V2 structure natively.
