# Phase 2F.3: Annotation Protocol Amendment Proposal

## Context and Justification
The original validation protocol for the Phase 2F human annotation required full exhaustive human annotation for all case-document pairs (10 cases x 248 documents = 2,480 explicit decisions). 

However, during the AI-assisted pilot (Phase 2F.2), it became evident that exhaustive row-by-row manual review of the entire corpus for each query is highly inefficient, as the vast majority of documents are entirely unrelated to the specific medical queries.

This amendment proposes formalizing an alternative approach: **Candidate-based human adjudication**.

## Comparison of Approaches

### Option A: Exhaustive Human Annotation
* **Method:** A human expert explicitly reviews and labels all 2,480 case-document pairs in the pilot (and tens of thousands in full production).
* **Pros:** Theoretically eliminates any possibility of false negatives missed by retrieval; provides a mathematically complete ground-truth matrix.
* **Cons:** Operationally intractable; forces human reviewers to spend 95%+ of their time labeling unambiguously irrelevant documents; prone to annotator fatigue and degraded quality on actual borderline cases.

### Option B: Candidate-Based Human Adjudication (Proposed)
* **Method:** Human reviewers evaluate a targeted subset of documents ("candidates") surfaced via intelligent discovery pipelines, plus any evidence manually discovered by the human. The remaining corpus is excluded via a formalized closure rule.
* **Pros:** Focuses human expertise on plausible evidence and difficult borderline cases; scales to full evaluation datasets.
* **Cons:** Relies on the comprehensiveness of the candidate generation step. If the candidate generation is flawed, false negatives may persist in the corpus.

## Specifications for Option B (Candidate-Based Adjudication)

To maintain rigorous ground-truth integrity under Option B, the following rules must be strictly defined and adhered to:

### 1. Candidate Generation
Candidates must be surfaced using high-recall, multi-strategy methods (e.g., BM25 keyword matching, dense vector semantic similarity, and entity co-occurrence graphs) to cast a wide net for any potentially relevant document.

### 2. Exhaustive Discovery Assessment
Candidate discovery is deemed exhaustively assessed when the retrieved candidate lists begin surfacing purely spurious matches (e.g., matching the word "mechanism" in a completely unrelated domain), indicating the semantic boundaries of the query have been exceeded.

### 3. False Negative Checking
A random sampling of exactly 5% of the "unsurfaced" corpus for each case must be subjected to an automated secondary screening using a reproducible random seed. 
The 5% sample is a **screening/assurance mechanism**, not independent proof of negative ground truth.
Allowed outputs from the screening are `POTENTIALLY_RELEVANT`, `UNCERTAIN`, and `PROBABLY_IRRELEVANT`.
Every `POTENTIALLY_RELEVANT` or `UNCERTAIN` result MUST be escalated to the human reviewer for independent adjudication.

### 3b. Critical Interpretation Rule
Never state that the 5% sample proved the remaining 95% is irrelevant, nor that no relevant documents exist in the unsurfaced corpus, unless the entire corpus was actually reviewed.
Instead, state: "No potentially relevant documents were identified in the sampled unsurfaced corpus under the specified secondary screening procedure, and all flagged/uncertain records were escalated to human review."


### 4. Case Closure Rule
A case is formally closed when all explicitly surfaced candidates have received a human decision, the false-negative check is passed, and the reviewer explicitly confirms NEW_EVIDENCE = NONE IDENTIFIED. 

### 5. NO_EVIDENCE vs. NOT_RELEVANT
* **NO_EVIDENCE**: The document is topically relevant to the query (e.g., discusses the correct drugs/pharmacology), but the available frozen source (often title-only) lacks a specific passage establishing the factual claim.
* **NOT_RELEVANT**: The document is substantively unrelated to the specific query.

### 6. Human Provenance Recording
Every human decision must record the reviewer's ID, a justification for the decision, the reviewer's confidence level, and an agreement/disagreement flag relative to any AI suggestion. 

### 7. AI Assistance Disclosure
Any resulting ground-truth dataset must carry a metadata flag designating it as **AI-assisted human annotation**, explicitly clarifying that an AI decision-helper surfaced the candidates and provided preliminary suggestions.

### 8. Validation Replacement
The requirement for a complete 2,480-row ground-truth submission is replaced by the requirement for a **Complete Surfaced-Candidate Audit Log**. The validator will check that all surfaced candidates have human labels and that the False Negative sampling protocol was executed, rather than demanding a label for every row in the corpus.