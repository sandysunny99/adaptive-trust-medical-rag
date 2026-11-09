> **WARNING: HISTORICAL / SUPERSEDED BY V3**
> This document is maintained for research provenance. For the current LIVE application provider status, refer to the V3 documents.

# TRACK_A_HUMAN_ANNOTATION_GUIDE_V2

## Purpose and Scope
This guide defines the standardized operating procedure for human annotators grading the relevance of retrieved evidence for pharmacological queries in the Track A dataset.

## A. What the Annotator is Judging
You are judging whether the provided `retrieved_evidence` chunk contains information that directly helps answer or ground the clinical/pharmacological query defined in `query_text`. You are evaluating the usefulness of the text *for a medical RAG system*, not just topical similarity.

## B. What Counts as Relevant (Grade 2)
The evidence chunk directly and specifically addresses the pharmacological query. It provides explicit interaction data, clearance pathways, contraindications, or risk assessments for the *exact drug entities* queried.

## C. What Counts as Partially Relevant (Grade 1)
The evidence chunk contains information about one or more queried entities or the general clinical context, but lacks the specific relationship, outcome, or interaction data required to fully answer the query. It provides useful background but cannot independently resolve the user's core question.

## D. What Counts as Irrelevant (Grade 0)
The evidence chunk does not address the queried entities or clinical question in any meaningful way. It may share words with the query but is clinically unrelated.

## E. How to Handle Ambiguous Evidence
If the text is malformed, entities are ambiguously resolved, or you cannot confidently determine relevance, select `AMBIGUOUS`. Do not guess. Ambiguous positions are routed to a secondary adjudication workflow.

## F. How to Handle Missing Abstracts
If `abstract_available` is `false`, and the remaining provided context is insufficient to determine clinical relevance, you must label the position `INSUFFICIENT_INFORMATION` (Grade 0). Do not attempt to search for the abstract externally or fabricate a judgment.

## G. Distinguishing Topical Similarity from Answer Relevance
Merely mentioning the drug names is not enough. If the query asks for a drug-drug interaction, an article that mentions both drugs in passing but discusses an unrelated surgical procedure is `PARTIALLY_RELEVANT` at best, or `IRRELEVANT` if the clinical context is totally unaligned.

## H. Using the Provided Query and Evidence
Base your judgment strictly on the text provided in the `retrieved_evidence` field against the `query_text`. Do not assume the LLM "could probably figure it out" if the text itself doesn't contain the data.

## I. Handling Pharmacology Terminology
Pay strict attention to drug formulations, routes of administration, and salt forms if specified in the query. Evidence for topical administration may not be relevant to a query explicitly asking about systemic intravenous administration.

## J. Recording Rationale
You must record a brief explanation in the `rationale` field justifying why you selected a particular label, especially for `PARTIALLY_RELEVANT` or `AMBIGUOUS` cases.

## K. Recording Evidence Spans
If the text is `RELEVANT` or `PARTIALLY_RELEVANT`, extract and copy the exact sub-string (evidence span) from the text that justifies your choice into the `evidence_span` field.

## L. Avoiding Source Authority Bias
Do not automatically assume a chunk is `RELEVANT` just because it comes from a highly authoritative journal. Even high-authority sources can be irrelevant to the specific query.

## M. Avoiding Ranking Bias
The positions are presented to you independently. Do not assume the first document is the most relevant or that later documents must be irrelevant. Judge each chunk entirely on its own merit.

## N. What to Do When Uncertain
When in doubt, use the `AMBIGUOUS` label and explain your uncertainty in the `rationale`. Do not force a grade if you lack the pharmacological expertise to interpret the text.
