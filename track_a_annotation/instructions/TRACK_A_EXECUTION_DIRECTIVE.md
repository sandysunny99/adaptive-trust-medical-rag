ANTIGRAVITY EXECUTION DIRECTIVE
TRACK A BATCH 004 HUMAN REVIEW -> COMMIT -> BATCH 005 PREPARATION

PROJECT:
Adaptive Trust-Aware Medical RAG

TRACK:
TRACK_A

CURRENT STAGE:
CONTROLLED SCIENTIFIC VALIDATION

============================================================
0. PURPOSE
============================================================

You have already received and permanently logged:

TRACK_A_CONSOLIDATED_WORKFLOW.md

Treat that file as the workflow standard.

However, before continuing execution, apply the sequencing correction in this instruction:

IMPORTANT:
The researcher-facing review files for Batch 004 must exist BEFORE
human annotation and BEFORE Batch 004 commit.

Do NOT wait until after commit to generate the Batch 004 human review
package.

The correct order is:

PREPARE REVIEW
→ HUMAN REVIEW
→ VALIDATE HUMAN DECISIONS
→ COMMIT
→ POST-COMMIT QC
→ PREPARE NEXT BATCH

Do not alter the scientific protocol.

============================================================
1. AUTHORITATIVE REPOSITORY STATE
============================================================

Use the existing repository files as authoritative.

DO NOT:

- recreate Track A
- recreate the benchmark
- change retrieval results
- change retrieved evidence
- change queries
- change position IDs
- change evidence IDs
- reopen Gate 5
- modify Phase 15
- modify historical committed annotations
- replace existing canonical evidence
- regenerate a different corpus
- change the benchmark ordering

Benchmark:

LOCKED

============================================================
2. CURRENT BATCH 004 STATE
============================================================

Batch:

TRACK_A_A_BATCH_004

Formal batch size:

60

Already committed:

20

Remaining for researcher review:

40

Existing review bundle:

TRACK_A_A_BATCH_004_REVIEW_BUNDLE_01

Remaining records:

Windows 03-06

Total remaining:

40

These 40 records must be treated as the current researcher
annotation workload.

Do not create another fragmented 10-record workflow.

============================================================
3. FIRST ACTION: READ AND AUDIT
============================================================

Before modifying anything, inspect:

1. master Track A annotation dataset
2. Batch 004 manifest
3. reservation registry
4. Batch 004 canonical JSON
5. existing Batch 004 Windows 03-06
6. existing Batch 004 Review Bundle 01
7. existing final human review matrix
8. existing raw human annotation artifacts
9. TRACK_A_CONSOLIDATED_WORKFLOW.md

Do not assume the filesystem state.

Verify actual repository state.

============================================================
4. BATCH 004 PRE-REVIEW ACCOUNTING
============================================================

Programmatically calculate:

TOTAL DATASET
ANNOTATED
UNANNOTATED
COMMITTED
RESERVED
UNRESERVED
ACTIVE RESERVED
BATCH 004 COMMITTED
BATCH 004 RESERVED
BATCH 004 UNANNOTATED

Expected Batch 004 state:

Batch 004 total = 60
Batch 004 already committed = 20
Batch 004 remaining review = 40

If the repository does not match this state:

STOP.

Do not repair automatically.

Report:

EXPECTED
ACTUAL
DISCREPANCY

============================================================
5. VERIFY THE EXACT 40 REMAINING RECORDS
============================================================

Identify exactly the 40 Batch 004 records that are:

- belonging to Batch 004
- RESERVED
- UNANNOTATED
- not already committed

Verify:

count = 40

IDs unique = PASS

all IDs exist in master = PASS

all IDs belong to Batch 004 = PASS

all IDs belong to Review Bundle 01 = PASS

no duplicate IDs = PASS

no cross-batch overlap = PASS

no already annotated positions = PASS

If any test fails:

STOP.

============================================================
6. QUERY REQUIREMENT SAFETY
============================================================

For EVERY record, derive query requirements independently from
the record's EXACT QUERY.

Never reuse previous query state.

Never carry:

previous_query_requirements

into another record.

For every record independently determine:

- entities
- relationship
- mechanism
- outcome
- context

Run explicit transition regression tests whenever the query changes.

For Batch 004 verify at minimum:

QUERY GROUP 1:

Concomitant use of warfarin and aspirin bleeding risk

Requirements:

Entity 1 = warfarin
Entity 2 = aspirin
Relationship = concomitant / co-use
Mechanism = N/A
Outcome = bleeding risk
Context = None specified


QUERY GROUP 2:

CYP2C9 interaction between fluconazole and warfarin

Requirements:

Entity 1 = fluconazole
Entity 2 = warfarin
Relationship = CYP2C9-mediated drug-drug interaction
Mechanism = CYP2C9
Outcome = interaction effect
Context = None specified

Regression:

Group 1 -> Group 2
Group 2 -> Group 1

Expected:

NO QUERY REQUIREMENT LEAKAGE

============================================================
7. SEMANTIC SAFETY FOR DDI ANNOTATION
============================================================

Maintain the strict pairwise rule.

Do not infer:

A-C

from:

A-B
+
B-C

For DDI relevance, the evidence must directly support the requested
drug pair unless the evidence explicitly establishes the queried
relationship.

Do not infer a queried interaction merely because:

- both drugs appear somewhere in the same document
- both are discussed in different examples
- one drug interacts with another drug
- a mechanism is mentioned generally
- the article is broadly about DDIs
- the evidence contains related pharmacology

The human researcher makes the final determination.

============================================================
8. BATCH 004 CONSOLIDATED REVIEW PACKAGE
============================================================

Prepare ONE researcher-facing file:

TRACK_A_A_BATCH_004_REMAINING_40_CONSOLIDATED_HUMAN_REVIEW.md

This file MUST be prepared BEFORE human confirmation.

It must contain exactly 40 records.

Internal structure:

WINDOW 03
Records 1-10

WINDOW 04
Records 11-20

WINDOW 05
Records 21-30

WINDOW 06
Records 31-40

Do not require the researcher to open four separate files.

============================================================
9. CONTENT REQUIRED FOR EVERY RECORD
============================================================

For each record include:

RECORD NUMBER

POSITION ID

BATCH

WINDOW

EXACT QUERY

QUERY REQUIREMENTS

EXACT RETRIEVED EVIDENCE

ABSTRACT STATUS

ABSTRACT TEXT WHEN ACTUALLY AVAILABLE

SOURCE METADATA

PROVENANCE

EVIDENCE ID

LLM ADVISORY ONLY

The LLM advisory section may contain:

- advisory label
- advisory rationale
- pairwise assessment
- mechanism assessment
- outcome assessment
- missing components
- supporting span

But explicitly state:

LLM ADVISORY ONLY
NOT HUMAN GROUND TRUTH

Then:

HUMAN DECISION

Human Label:
[BLANK]

Human Score:
[BLANK]

Human Exact Supporting Span:
[BLANK]

Researcher Notes:
[BLANK]

============================================================
10. HUMAN LABEL ISOLATION
============================================================

Before the researcher responds:

Human labels = 0

Human scores = 0

Human spans = 0

Human notes = 0

Automatic human decisions = 0

Do NOT populate any of these fields.

Do not transform advisory labels into human labels.

Do not make "suggested" human decisions.

============================================================
11. BATCH 004 RAW DATA FILE
============================================================

Prepare ONE raw-data file BEFORE human review:

TRACK_A_A_BATCH_004_REMAINING_40_RAW_DATA.md

This file must contain the exact raw information needed for
researcher analysis.

For every record include:

position_id
batch_id
window
exact query
query requirements
evidence_id
exact retrieved evidence
abstract status
abstract text if available
source metadata
provenance
evidence location metadata when available

The retrieved evidence must remain VERBATIM.

Do not:

- summarize instead of providing evidence
- paraphrase the evidence
- truncate the evidence
- normalize wording
- fabricate missing abstracts
- fabricate provenance
- fabricate source data

The raw-data file must remain evidence-preserving.

============================================================
12. HUMAN CONFIRMATION TEMPLATE
============================================================

At the bottom of the consolidated review file provide ONE response
template containing all 40 records.

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

Continue through:

40. POSITION_ID

Do not split the response by window.

============================================================
13. EXACT SPAN RULE
============================================================

For human-selected:

RELEVANT
or
PARTIALLY_RELEVANT

the supporting span must be:

- literal
- contiguous
- present in retrieved_evidence
- unmodified
- non-paraphrased

Do not combine disconnected fragments.

Do not manufacture spans.

For:

IRRELEVANT
INSUFFICIENT_INFORMATION

empty span is acceptable when no qualifying evidence span exists.

For:

AMBIGUOUS

empty span is acceptable when accompanied by an explanatory note.

============================================================
14. PRE-REVIEW QC
============================================================

Before giving the review file to the researcher, run:

POSITION COUNT = 40

UNIQUE IDS = PASS

MASTER MEMBERSHIP = PASS

BATCH MEMBERSHIP = PASS

RESERVATION = PASS

UNANNOTATED = PASS

CROSS-BATCH DUPLICATE CHECK = PASS

QUERY PRESERVATION = PASS

EVIDENCE PRESERVATION = PASS

ABSTRACT PRESERVATION = PASS

PROVENANCE PRESERVATION = PASS

QUERY REQUIREMENTS = PASS

QUERY TRANSITION REGRESSION = PASS

HUMAN LABELS PREFILLED = 0

HUMAN SPANS PREFILLED = 0

AUTOMATIC HUMAN DECISIONS = 0

BENCHMARK = LOCKED

The researcher-facing package is READY only when every required
check passes.

============================================================
15. IMPORTANT: DO NOT COMMIT YET
============================================================

After preparing the 40-record consolidated review package:

STOP AT:

HUMAN ANNOTATION SESSION

Do not:

- commit Batch 004
- alter master annotations
- alter reservation registry
- generate Batch 005
- make automatic decisions

until the researcher returns the HUMAN_CONFIRMATION block.

============================================================
16. WHEN HUMAN_CONFIRMATION IS RECEIVED
============================================================

Parse the response.

Require:

exactly 40 position IDs

all IDs belong to Batch 004

no duplicate IDs

no missing IDs

no extra IDs

valid labels

correct scores

exact spans valid where required

Researcher notes preserved

Allowed mapping:

RELEVANT = 2
PARTIALLY_RELEVANT = 1
IRRELEVANT = 0
INSUFFICIENT_INFORMATION = 0
AMBIGUOUS = null

Do NOT silently correct invalid responses.

If invalid:

STOP.

Report each invalid record.

============================================================
17. BATCH 004 COMMIT
============================================================

Only when all 40 researcher decisions pass validation:

Commit ONLY the appropriate human annotation fields.

Do not modify:

query_text
retrieved_evidence
position_id
evidence_id
source evidence
benchmark
retrieval results
historical records

Registry transition:

Batch 004:
RESERVED
->
COMMITTED

Expected final state:

Batch 004 = 60/60 COMMITTED

============================================================
18. POST-COMMIT QC
============================================================

After commit verify:

Batch 004 committed = 60

Previously committed = 20 preserved

Newly committed = 40

Remaining Batch 004 = 0

Duplicate annotations = 0

Cross-batch accidental modifications = 0

Evidence integrity = PASS

Query integrity = PASS

Span integrity = PASS

Registry transition = PASS

Benchmark = LOCKED

Create:

TRACK_A_A_BATCH_004_HUMAN_COMMIT_FINAL.md

TRACK_A_A_BATCH_004_POST_COMMIT_QC.md

These are POST-COMMIT artifacts.

IMPORTANT:

Do not regenerate or replace the already-used researcher review
package after commit.

The original pre-review package must remain preserved.

============================================================
19. ONLY AFTER BATCH 004 POST-COMMIT QC PASSES
============================================================

Run a fresh global dataset accounting.

Calculate:

TOTAL DATASET
ANNOTATED
UNANNOTATED
COMMITTED
RESERVED
UNRESERVED
ACTIVE RESERVED
UNREVIEWED

Do NOT assume any counts.

Read them directly from the current repository.

============================================================
20. SELECT BATCH 005
============================================================

Select exactly 60 eligible positions satisfying:

annotation_status = UNANNOTATED

AND

not currently RESERVED

AND

not committed

AND

not assigned to another active batch

Selection must be deterministic.

Preserve canonical order.

Do not randomize merely for diversity.

============================================================
21. BATCH 005 INTERNAL STRUCTURE
============================================================

Create:

60 total positions

6 internal windows

10 records each

WINDOW 01
WINDOW 02
WINDOW 03
WINDOW 04
WINDOW 05
WINDOW 06

These windows are for auditability only.

============================================================
22. BATCH 005 RESEARCHER-FACING PACKAGE
============================================================

Create ALL of the following in ONE generation operation:

1.
TRACK_A_A_BATCH_005_CONSOLIDATED_HUMAN_REVIEW.md

2.
TRACK_A_A_BATCH_005_RAW_DATA.md

3.
TRACK_A_A_BATCH_005.json

4.
TRACK_A_A_BATCH_005_INTEGRITY_AUDIT.md

5.
TRACK_A_A_BATCH_005_HUMAN_CONFIRMATION_TEMPLATE.md
if not already included inside the consolidated review file

6.
TRACK_A_A_BATCH_005_RESERVATION_STATUS.md

Do not make the researcher request the raw-data file separately.

============================================================
23. BATCH 005 CONSOLIDATED HUMAN REVIEW
============================================================

The main researcher-facing file must contain all 60 records.

Structure:

SECTION A:
Batch accounting

SECTION B:
60-record summary table

SECTION C:
WINDOW 01
Records 1-10

SECTION D:
WINDOW 02
Records 11-20

SECTION E:
WINDOW 03
Records 21-30

SECTION F:
WINDOW 04
Records 31-40

SECTION G:
WINDOW 05
Records 41-50

SECTION H:
WINDOW 06
Records 51-60

SECTION I:
ONE HUMAN_CONFIRMATION template

The researcher must be able to perform the complete annotation using
this single consolidated file.

============================================================
24. BATCH 005 RAW DATA
============================================================

The raw-data MD file must contain the FULL exact retrieved evidence
for all 60 records.

Do not replace it with evidence summaries.

Do not truncate evidence.

Do not fabricate missing metadata.

Preserve exact source fields.

============================================================
25. BATCH 005 HUMAN DECISION ISOLATION
============================================================

Before researcher review:

human labels = blank

human scores = blank

human spans = blank

researcher notes = blank

automatic human decisions = 0

LLM advisory remains advisory only.

============================================================
26. FINAL BATCH 005 PREPARATION QC
============================================================

Require:

60 positions = PASS

unique IDs = PASS

master membership = PASS

unannotated = PASS

reservation = PASS

no cross-batch duplicates = PASS

query preservation = PASS

evidence preservation = PASS

abstract preservation = PASS

provenance preservation = PASS

query requirements = PASS

query-boundary regression = PASS

human labels prefilled = 0

human spans prefilled = 0

automatic human decisions = 0

benchmark = LOCKED

============================================================
27. DO NOT START BATCH 005 COMMIT
============================================================

After creating Batch 005:

STOP.

Final state:

BATCH_004 = COMPLETE / COMMITTED

BATCH_005 = RESERVED / READY_FOR_HUMAN_REVIEW

Do not annotate Batch 005 automatically.

Do not commit Batch 005.

Do not generate another batch.

Wait for researcher review.

============================================================
28. OUTPUT REPORT
============================================================

At the end produce a machine-readable execution summary.

Expected structure:

TRACK_A_BATCH_004
=================
Total: 60
Previously committed: 20
Human-reviewed this cycle: 40
Final committed: 60/60
Remaining: 0
Automatic human decisions: 0
Post-commit QC: PASS
Benchmark: LOCKED

TRACK_A_BATCH_005
=================
Formal batch size: 60
Windows: 6 x 10
Consolidated review: CREATED
Raw data MD: CREATED
Manifest: CREATED
Integrity audit: PASS
Human labels prefilled: 0
Human spans prefilled: 0
Automatic human decisions: 0
Status: READY_FOR_HUMAN_REVIEW
Benchmark: LOCKED

============================================================
29. CRITICAL FILE ORDER
============================================================

BATCH 004:

PRE-REVIEW:
- consolidated human review
- raw data MD

HUMAN:
- researcher confirmation

POST-REVIEW:
- validation
- commit

POST-COMMIT:
- commit final
- QC report

THEN:

BATCH 005:
- manifest
- reservation
- consolidated review
- raw data
- integrity audit
- human confirmation template

THEN STOP.

============================================================
30. NON-NEGOTIABLE RULE
============================================================

ONE BATCH FOR THE RESEARCHER:

ONE consolidated review file
ONE raw-data MD file
ONE human response

INTERNAL:

6 x 10 windows

AFTER HUMAN RESPONSE:

ONE validation
ONE commit
ONE post-commit QC

THEN:

NEXT BATCH PREPARATION

No fragmented researcher workflow.

No automatic human annotation.

No silent corrections.

No evidence modification.

No query modification.

No benchmark modification.

END DIRECTIVE
