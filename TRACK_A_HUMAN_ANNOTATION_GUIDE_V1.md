# TRACK_A_HUMAN_ANNOTATION_GUIDE_V1

## Overview
You are annotating retrieved biomedical evidence chunks for a Pharmacological RAG pipeline evaluation. Your task is to determine how relevant a retrieved text chunk is to a specific medical query.

## What You Will See
For each evaluation position, you will be provided:
- **Query**: The specific pharmacological question (e.g., "Clearance pathway for lisinopril").
- **Evidence Context**: The retrieved document's title and the specific enriched text chunk retrieved by the system.
- **Publication Metadata**: Date and source.

## Relevance Criteria
Relevance is strictly defined by whether the chunk helps answer the exact query regarding the specific drug entities and relationships mentioned.

- **Drug/Entity Alignment**: The text must match the specific drug (or exact class if the query is broad) and the exact population context.
- **Relationship/ADE**: If the query asks about a drug-drug interaction (DDI) or adverse drug event (ADE), the text must address that interaction, not just mention both drugs.

## Allowed Labels (Graded Relevance)
Assign ONE of the following labels to each chunk:
1. **RELEVANT (Grade 2)**: Directly and specifically answers or supports answering the query. Contains explicit pharmacological data, pathways, or interactions regarding the queried entities.
2. **PARTIALLY_RELEVANT (Grade 1)**: Mentions the queried entities in a related context but lacks the specific interaction, pathway, or outcome data requested by the query.
3. **IRRELEVANT (Grade 0)**: Does not address the query or the entities in a meaningful way.
4. **INSUFFICIENT_INFORMATION (Grade 0)**: Mentions the entities but provides no pharmacological substance (e.g., just a title, or a methodology section without results).
5. **AMBIGUOUS**: You cannot confidently determine relevance due to malformed text or highly ambiguous medical terminology.

## Handling Special Cases
- **Missing Abstracts/Context**: If the text is fundamentally incomplete (e.g., "ABSTRACT_NOT_AVAILABLE"), mark it as `INSUFFICIENT_INFORMATION` unless the title alone conclusively provides the exact answer (rare). If unsure, mark `AMBIGUOUS`.
- **Contradictory Evidence**: Evidence that contradicts the established clinical consensus is still **RELEVANT** if it directly addresses the query. Relevance is about topical alignment, not truthfulness.

## Adjudication & Concordance
- All chunks marked `AMBIGUOUS` will be routed to a secondary senior annotator.
- 10% of the dataset will be dual-annotated. Inter-annotator agreement (Cohen's Kappa) must exceed 0.70.
- Discordant ties will be resolved via discussion and recorded in the adjudication log.
