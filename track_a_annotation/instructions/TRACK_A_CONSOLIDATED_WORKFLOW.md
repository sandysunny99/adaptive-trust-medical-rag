ANTIGRAVITY MASTER INSTRUCTION
TRACK A ANNOTATION CONTINUATION
BATCH 004 COMPLETION -> NEXT BATCH CONSOLIDATED REVIEW PACKAGE

PROJECT:
Adaptive Trust-Aware Medical RAG
Track:
TRACK_A
Task:
Researcher-controlled retrieval relevance annotation

============================================================
1. CURRENT AUTHORITATIVE STATE
============================================================

Use the existing repository state as authoritative.

Do NOT recreate the benchmark.
Do NOT alter the retrieval corpus.
Do NOT modify query_text.
Do NOT modify retrieved_evidence.
Do NOT modify evidence IDs.
Do NOT modify position_ids.
Do NOT reopen historical gates.
Do NOT alter Gate 5.
Do NOT alter Phase 15.
Do NOT modify the retrieval benchmark.

Benchmark state:
LOCKED

Batch 004 is already partially completed.

Current Batch 004 structure:
- Formal batch size: 60
- Already committed: 20
- Remaining in Batch 004 for researcher review: 40
- Existing remaining positions correspond to the prepared review bundle:
  TRACK_A_A_BATCH_004_REVIEW_BUNDLE_01
- Existing review records are the records from Batch 004 Windows 03-06.

The pasted review matrix confirms that the human decision fields remain BLANK and that the LLM advisory is only advisory. Do not convert advisory labels into human decisions.

============================================================
2. PRIMARY OBJECTIVE
============================================================

FIRST:

Complete the remaining 40 uncommitted / unreviewed records belonging to:

TRACK_A_A_BATCH_004

Do NOT create another fragmented human-review workflow for these 40 records.

Present the complete remaining Batch 004 set as ONE consolidated researcher review package.

The researcher should receive all remaining 40 records in one file/package, while the underlying formal 10-record window structure must remain preserved internally for auditability.

After the researcher supplies the human decisions:

1. Validate the decisions.
2. Commit Batch 004.
3. Verify the commit.
4. Confirm Batch 004 is fully COMMITTED.
5. Only after successful Batch 004 commit, generate the next Track A annotation batch.

============================================================
3. BATCH 004: CONSOLIDATED REVIEW REQUIREMENT
============================================================

Create ONE authoritative human-review presentation file containing:

Records:
All 40 remaining uncommitted/unreviewed Batch 004 records.

Do NOT make the researcher open:
- Window 03 separately
- Window 04 separately
- Window 05 separately
- Window 06 separately

Those window files may remain in the repository for formal audit purposes, but the researcher-facing review must be consolidated.

The consolidated review file must preserve this order:

Window 03:
Records 1-10

Window 04:
Records 11-20

Window 05:
Records 21-30

Window 06:
Records 31-40

Do NOT reorder records unless the canonical batch ordering proves that the existing order is different.

============================================================
4. EACH RECORD MUST CONTAIN
============================================================

For EVERY record include all of the following:

RECORD NUMBER

POSITION ID

BATCH ID

WINDOW ID

EXACT QUERY

QUERY REQUIREMENTS

- Entity 1 / entities
- Entity 2 when applicable
- Relationship
- Mechanism
- Outcome
- Context

EXACT RETRIEVED EVIDENCE

ABSTRACT STATUS

ABSTRACT TEXT
- Include it when actually available.
- Do not fabricate an abstract.
- If unavailable, explicitly state NOT AVAILABLE.

SOURCE METADATA

PROVENANCE
- Preserve actual value.
- If unavailable, explicitly state NOT AVAILABLE.

LLM ADVISORY ONLY

Include:
- advisory label
- advisory reasoning
- pairwise relationship assessment
- mechanism assessment
- outcome assessment
- missing component
- exact supporting span

IMPORTANT:
Clearly mark this as:

LLM ADVISORY ONLY
NOT HUMAN GROUND TRUTH

Then provide:

HUMAN DECISION

Human Label:
[BLANK]

Human Score:
[BLANK]

Human Exact Supporting Span:
[BLANK]

Researcher Notes:
[BLANK]

DO NOT pre-fill any human decision.

============================================================
5. HUMAN LABEL DEFINITIONS
============================================================

Use the locked Track A definitions exactly.

RELEVANT = 2

Use when the evidence directly addresses the exact query and its required relationship/outcome.

PARTIALLY_RELEVANT = 1

Use when the evidence has meaningful overlap with the query or clinical context but does not fully establish the requested relationship/outcome.

IRRELEVANT = 0

Use when the evidence does not meaningfully address the requested query.

INSUFFICIENT_INFORMATION = 0

Use when the evidence contains potentially related entities/context but does not contain enough substantive information to determine the requested relationship/outcome.

AMBIGUOUS = null

Use when the evidence or record is genuinely ambiguous, malformed, or cannot be confidently adjudicated from the supplied evidence.

Do NOT infer a pairwise relationship from separate relationships.

Example:

A-B exists
B-C exists

This does NOT establish:

A-C

For DDI queries, require direct evidence for the requested pair unless the evidence explicitly establishes the queried relationship.

============================================================
6. EXACT SPAN RULE
============================================================

If a human selects:

RELEVANT
or
PARTIALLY_RELEVANT

the exact supporting span must be copied literally from the retrieved evidence.

The span must:

- be contiguous
- exist literally in retrieved_evidence
- not paraphrase
- not summarize
- not combine multiple disconnected fragments
- not introduce text absent from the evidence

For:

IRRELEVANT
INSUFFICIENT_INFORMATION

the human span may remain empty when there is no qualifying supporting span.

For:

AMBIGUOUS

allow an empty span with an explanatory researcher note.

============================================================
7. CRITICAL ANNOTATION ISOLATION
============================================================

Antigravity must never do the following:

- fill HUMAN_FINAL_LABEL automatically
- fill HUMAN_FINAL_SCORE automatically
- fill HUMAN_FINAL_SPAN automatically
- convert LLM advisory to human annotation
- silently correct researcher decisions
- infer what the researcher "probably meant"
- overwrite researcher notes
- generate synthetic human labels

LLM analysis is advisory only.

Human decisions are researcher-controlled.

============================================================
8. QUERY REQUIREMENT SAFETY CHECK
============================================================

Before presenting the review file, programmatically verify every record.

For each record:

requirements = derive_from_exact_query(record.query_text)

Never carry query requirements from the previous record.

This is especially important when the query changes between groups.

For the current Batch 004 dataset, independently verify the two query groups.

Query group 1:

Concomitant use of warfarin and aspirin bleeding risk

Expected requirements:

Entity 1:
warfarin

Entity 2:
aspirin

Relationship:
concomitant / co-use

Outcome:
bleeding risk

Mechanism:
N/A

Query group 2:

CYP2C9 interaction between fluconazole and warfarin

Expected requirements:

Entity 1:
fluconazole

Entity 2:
warfarin

Relationship:
CYP2C9-mediated drug-drug interaction

Mechanism:
CYP2C9

Outcome:
interaction effect

Context:
None specified

Run a transition regression check:

Group 1 -> Group 2
Group 2 -> Group 1

Confirm that no requirements leak across query boundaries.

If any mismatch exists:
STOP.
Do not present the review package.
Do not modify canonical data.
Report the mismatch.

============================================================
9. PRE-REVIEW INTEGRITY AUDIT
============================================================

Before generating the researcher package, verify:

- exactly 40 records
- all IDs unique
- all IDs exist in master
- all IDs belong to Batch 004
- all 40 are currently UNANNOTATED
- all 40 are RESERVED
- all 40 belong to the correct Batch 004 reservation
- no ID belongs to another batch
- no duplicate IDs
- no evidence changes
- no query changes
- no source metadata changes
- no abstract fabrication
- no human labels present
- no human spans present
- benchmark remains LOCKED

Also verify:

master query == canonical batch query

master evidence == canonical batch evidence

master position_id == canonical batch position_id

The consolidated review package must be presentation-only.
It must not modify authoritative records.

============================================================
10. FINAL CONSOLIDATED BATCH 004 REVIEW FILE
============================================================

Create ONE file with a clear name similar to:

TRACK_A_A_BATCH_004_REMAINING_40_CONSOLIDATED_HUMAN_REVIEW.md

This must contain all 40 remaining records in one file.

At the beginning include:

# TRACK A BATCH 004
# CONSOLIDATED HUMAN REVIEW PACKAGE

Batch:
TRACK_A_A_BATCH_004

Records:
40 remaining

Status:
RESERVED / UNANNOTATED / AWAITING HUMAN REVIEW

Benchmark:
LOCKED

Human annotations:
0

LLM advisory:
ADVISORY ONLY

Then include a compact summary table:

| # | Position ID | Window | Exact Query | Advisory | Missing Component | Human Label |
|---|-------------|--------|-------------|----------|-------------------|-------------|

Human Label must remain BLANK.

Then provide the complete detailed records.

============================================================
11. HUMAN RESPONSE TEMPLATE
============================================================

At the end of the ONE consolidated file create one response template containing ALL 40 positions.

Format:

HUMAN_CONFIRMATION
TRACK: TRACK_A
BATCH: TRACK_A_A_BATCH_004
BUNDLE: TRACK_A_A_BATCH_004_REVIEW_BUNDLE_01

1. POSITION_ID
   LABEL:
   SCORE:
   EXACT_SPAN:
   NOTES:

2. POSITION_ID
   LABEL:
   SCORE:
   EXACT_SPAN:
   NOTES:

Continue through record 40.

Do not force the researcher to respond separately per window.

The goal is:

ONE REVIEW FILE
ONE HUMAN RESPONSE
ONE VALIDATION
ONE COMMIT

============================================================
12. RAW DATA REQUIREMENT
============================================================

At the final stage of preparing Batch 004, create a SECOND file specifically for raw review/analysis.

Required filename:

TRACK_A_A_BATCH_004_REMAINING_40_RAW_DATA.md

This file must contain the raw evidence required for human decision-making without replacing or summarizing the original evidence.

For each of the 40 records include:

- position_id
- batch_id
- window
- exact query
- exact query requirements
- evidence_id
- exact retrieved evidence
- abstract status
- abstract text when available
- source metadata
- provenance
- evidence location metadata when present

Also include the LLM advisory separately and clearly mark it:

ADVISORY ONLY
NOT HUMAN GROUND TRUTH

Do not let the raw-data file become a prediction file.

Do not put final human labels into it before the researcher provides them.

============================================================
13. DO NOT DUPLICATE OR TRANSFORM EVIDENCE
============================================================

The raw data file must preserve evidence verbatim.

No:

- summarization replacing evidence
- paraphrasing replacing evidence
- truncation
- normalization that changes wording
- inferred missing abstracts
- inferred provenance
- fabricated source information

It is acceptable to provide an Evidence Summary in the presentation layer, but the raw-data file must contain the full exact retrieved evidence.

============================================================
14. HUMAN REVIEW COMPLETION
============================================================

When the researcher returns the 40 human decisions:

First parse the response.

Validate:

- exactly 40 position IDs
- all IDs belong to Batch 004
- no duplicates
- every requested field is present
- labels are valid
- score matches label
- exact span matches retrieved evidence when required
- no extra position IDs
- no missing position IDs

Allowed mapping:

RELEVANT -> 2
PARTIALLY_RELEVANT -> 1
IRRELEVANT -> 0
INSUFFICIENT_INFORMATION -> 0
AMBIGUOUS -> null

Do not silently repair invalid decisions.

If invalid:
STOP and report exactly which records are invalid.

============================================================
15. BATCH 004 COMMIT GATE
============================================================

Only after all 40 human decisions pass validation:

Commit the 40 researcher decisions.

Transition:

Batch 004 RESERVED
        ->
Batch 004 COMMITTED

Update only the appropriate annotation fields.

Do not alter:

query
retrieved_evidence
position_id
evidence_id
benchmark
retrieval outputs
historical records

After commit, run a complete post-commit audit.

Required checks:

- Batch 004 committed count = 60/60
- previous 20 remain committed
- newly committed = 40
- duplicate annotations = 0
- uncommitted Batch 004 positions = 0
- accidental modifications outside Batch 004 = 0
- evidence integrity PASS
- query integrity PASS
- span integrity PASS
- reservation registry transition PASS
- benchmark LOCKED

============================================================
16. BATCH 004 FINAL OUTPUTS
============================================================

After successful commit create:

1.
TRACK_A_A_BATCH_004_HUMAN_COMMIT_FINAL.md

2.
TRACK_A_A_BATCH_004_POST_COMMIT_QC.md

3.
TRACK_A_A_BATCH_004_REMAINING_40_CONSOLIDATED_HUMAN_REVIEW.md

4.
TRACK_A_A_BATCH_004_REMAINING_40_RAW_DATA.md

The first two document the commit and QC.

The latter two are the researcher review artifacts.

Do not overwrite the original review bundle.

============================================================
17. ONLY AFTER BATCH 004 SUCCESSFUL COMMIT:
GENERATE NEXT BATCH
============================================================

Now perform a fresh global accounting audit.

Calculate:

TOTAL DATASET
ANNOTATED
RESERVED
COMMITTED
UNANNOTATED
UNRESERVED
UNREVIEWED

Then identify:

ALL positions that are:

annotation_status = UNANNOTATED
AND
not currently RESERVED
AND
not committed
AND
not already assigned to another active batch

These are the eligible next positions.

============================================================
18. NEXT BATCH MUST BE ONE CONSOLIDATED HUMAN REVIEW PACKAGE
============================================================

Create the next formal Track A batch using the normal formal batch size:

60 positions

Preserve the existing internal audit structure:

6 formal windows x 10 records

BUT:

Do NOT make the researcher review six separate files.

Create ONE consolidated researcher-facing review file containing all 60 records.

Example filename:

TRACK_A_A_BATCH_005_CONSOLIDATED_HUMAN_REVIEW.md

The file must contain:

Records 1-60

with internal section markers:

WINDOW 01
WINDOW 02
WINDOW 03
WINDOW 04
WINDOW 05
WINDOW 06

This keeps auditability while giving the researcher ONE file.

============================================================
19. NEXT BATCH RAW DATA FILE
============================================================

At the same time create:

TRACK_A_A_BATCH_005_RAW_DATA.md

This must contain the complete exact raw data required for human review.

Do this in the same generation run.

Do NOT make the researcher request the raw data separately.

============================================================
20. "ONE SINGLE GO" OUTPUT REQUIREMENT
============================================================

For every future batch after Batch 004:

Generate the following together in ONE preparation operation:

A. consolidated human review file

B. raw data MD file

C. batch manifest JSON

D. batch integrity audit MD

E. human confirmation response template

F. reservation status report

The researcher should receive one consolidated review package.

Internally, maintain the formal 10-record windows.

Externally, present one file for review.

============================================================
21. FUTURE BATCH SELECTION RULE
============================================================

Never select:

- annotated positions
- committed positions
- currently reserved positions
- positions already assigned to another active batch

Selection must be deterministic.

Preserve canonical dataset ordering unless the existing batch-selection protocol explicitly requires another deterministic ordering.

Do not randomly reshuffle positions merely to create a new batch.

============================================================
22. FUTURE BATCH QUERY GROUP CONTROL
============================================================

For every new batch:

Derive query requirements independently for EVERY record.

Never maintain state such as:

previous_query_requirements

and reuse it for the next record.

Every record must independently derive:

entities
relationship
mechanism
outcome
context

from its own exact query.

Run a query-transition regression test across every query boundary.

============================================================
23. FUTURE BATCH REVIEW PRESENTATION
============================================================

The consolidated review file should contain:

SECTION A:
Batch accounting

SECTION B:
Compact 60-record summary matrix

SECTION C:
Window 01 records 1-10

SECTION D:
Window 02 records 11-20

SECTION E:
Window 03 records 21-30

SECTION F:
Window 04 records 31-40

SECTION G:
Window 05 records 41-50

SECTION H:
Window 06 records 51-60

SECTION I:
Human confirmation template for all 60 records

Do not hide the raw evidence behind links to separate files.

The consolidated file itself should be sufficient for the researcher to perform the annotation.

============================================================
24. RESEARCHER DECISION INDEPENDENCE
============================================================

Every review package must make this explicit:

LLM advisory is NOT human ground truth.

The researcher must independently judge the retrieved evidence against the exact query.

The package may show:

- advisory label
- missing components
- pairwise assessment
- mechanism assessment
- outcome assessment

but the researcher remains the final decision-maker.

Do not display downstream benchmark predictions, trust scores, model rankings, or experiment outcomes in a way that could bias the relevance decision unless explicitly required by the locked protocol.

============================================================
25. FINAL QC FOR EVERY FUTURE BATCH
============================================================

Before declaring a batch ready for human review:

POSITION COUNT:
PASS

UNIQUE IDS:
PASS

MASTER MEMBERSHIP:
PASS

UNANNOTATED:
PASS

RESERVATION:
PASS

NO CROSS-BATCH DUPLICATES:
PASS

QUERY PRESERVATION:
PASS

EVIDENCE PRESERVATION:
PASS

ABSTRACT PRESERVATION:
PASS

PROVENANCE PRESERVATION:
PASS

QUERY REQUIREMENTS:
PASS

QUERY-BOUNDARY REGRESSION:
PASS

HUMAN LABELS:
0 PRE-FILLED

HUMAN SPANS:
0 PRE-FILLED

AUTOMATIC HUMAN DECISIONS:
0

BENCHMARK:
LOCKED

============================================================
26. IMPORTANT STOP CONDITIONS
============================================================

STOP immediately if:

- Batch 004 is not fully accounted for
- any of the 40 IDs are missing
- duplicate IDs exist
- any record is already annotated
- reservation state is inconsistent
- evidence changed
- query changed
- query requirements mismatch
- abstract was fabricated
- human label is pre-filled
- human span is pre-filled
- advisory is being treated as final
- Batch 004 commit validation fails

Do NOT "fix" the source data silently.

Report the exact failure and wait.

============================================================
27. FINAL CONSOLE SUMMARY
============================================================

At the end print a concise machine-readable summary.

Example:

TRACK_A_BATCH_004_COMPLETION
============================
Batch 004 total: 60
Already committed: 20
Reviewed/committed this operation: 40
Batch 004 final committed: 60/60
Remaining Batch 004: 0
Human decisions automatic: 0
Benchmark: LOCKED
Commit QC: PASS

NEXT_BATCH_PREPARATION
======================
Next batch: TRACK_A_A_BATCH_005
Formal size: 60
Consolidated review file: CREATED
Raw data MD: CREATED
Manifest: CREATED
Integrity audit: PASS
Human labels prefilled: 0
Benchmark: LOCKED

FINAL STATUS
============
BATCH_004: COMPLETE
BATCH_005: READY_FOR_HUMAN_REVIEW

============================================================
28. MOST IMPORTANT WORKFLOW RULE
============================================================

DO NOT repeatedly make me ask for:

- another window
- another review file
- another raw-data file
- another decision template

For each batch, prepare the complete researcher package in one operation.

FORMAL INTERNAL STRUCTURE:
60 positions
6 x 10 windows

RESEARCHER-FACING STRUCTURE:
ONE consolidated review file
ONE raw-data MD file
ONE human response template

After human decisions:
ONE validation
ONE commit
ONE post-commit QC

Then automatically prepare the next batch package using the same controlled structure.

END OF INSTRUCTION
