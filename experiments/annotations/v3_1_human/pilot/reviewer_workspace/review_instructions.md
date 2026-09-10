# Human Review Workflow & Instructions

## Workflow
1. Open `reviewer_A_case_review.csv`. It is grouped by `case_id`.
2. For each case, the strongest AI-surfaced candidates appear at the top.
3. Read the query and the actual frozen source text (`document_text` or via `documents.json`).
4. **MAKE YOUR INDEPENDENT DECISION.** Do not blindly trust the AI suggestion.
5. Fill out the `human_` fields (label, evidence span, rationale, confidence, agreement, reviewer ID, timestamp).
6. Update `review_progress.csv` manually as a tracker if desired.

## AI Suggestions vs Human Fields
Visually, the file separates `---AI_SUGGESTION---` and `---HUMAN_DECISION---`. The human decision fields MUST be filled.

## Adding Missing Evidence
If the AI missed a document and you found it manually in the corpus: simply find its row in the file or append a new row, and mark `human_agreement = NEW_EVIDENCE`.

## Note on Current Requirements
Currently, the frozen protocol demands all 2,480 rows be explicitly labeled. See `reports/audit/v3_1_pilot_scope_proposal.md` for a pending proposal to reduce this burden.
