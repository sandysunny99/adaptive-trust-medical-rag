# NLI_EVAL_SET_V1 independent review protocol (version 1, 2026-10-26)

**Status of the set:** `UNREVIEWED`. All 42 labels were written by an AI assistant (`label_origin:
audit_author_ai`). They are not clinician-reviewed and are not ground truth. Until this review is
completed by an independent, qualified person, every result computed on the set is exploratory.

## Who may review

- **Who qualifies:** a person with pharmacology or clinical training who did not write the labels.
- **Who doesn't:** no AI model can certify these labels, least of all the one that wrote them.
- **Adjudication:** a second person settles disagreements.

## Stage 1: blind labelling (`REVIEW_STAGE1_BLIND_V1.csv`)

1. **What to read:** for each row, the evidence text (an exact DailyMed label section) and the claim.
   Nothing else: no proposed label, no model score.
2. **Question:** does this evidence text, on its own, support the claim? Record one of:
   - `ENTAILMENT`: the text states or directly implies the claim;
   - `NEUTRAL`: the text does not state it; this includes claims that are true but not in this section;
   - `CONTRADICTION`: the text states the opposite;
   - `AMBIGUOUS`: reasonable readings disagree;
   - `INSUFFICIENT_CONTEXT`: the excerpt alone is not enough to decide.
3. **Recording:** write a one-line rationale and your reviewer id and date. Do not open the stage 2 sheet
   until every stage 1 row is done.

## Stage 2: comparison and adjudication (`REVIEW_STAGE2_ADJUDICATION_V1.csv`)

1. **Compare:** copy each stage 1 label into the stage 2 row and mark `agrees`.
2. **Adjudicate:** for each disagreement, the adjudicator records the final label and the reason. Disagreements
   are kept, not overwritten.

## After review

- **Original set untouched:** `NLI_EVAL_SET_V1.jsonl` (SHA-256 `bd23fe48…f4ff`) is frozen and is never edited.
- **Corrections:** reviewed labels go into a new version, `NLI_EVAL_SET_V2`, with a change log listing every
  changed example, its old and new label, the reviewer and the reason.
- **When results count:** only after that does the set's `review_status` become `REVIEWED`. Only a
  reviewed version may inform a model decision, and even then it is a small engineering benchmark, not a
  clinical accuracy estimate.

## Current blocker

No independent qualified reviewer has been assigned. The packet is ready, and the set stays `UNREVIEWED`.
