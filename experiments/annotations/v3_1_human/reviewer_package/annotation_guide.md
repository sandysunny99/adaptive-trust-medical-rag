# V3.1-HUMAN Annotation Guide v2

## Objective
Judge whether a document actually supports the clinical information need expressed by the query. Do not judge based solely on shared drug names, keywords, or topical similarity.

## Workflow
1. **Initial State**: All candidate combinations are marked `PENDING`.
2. **Review**: Evaluate the documents for each case. You may use text search to find synonyms/abbreviations. Do not reject a document merely because it uses clinically equivalent terminology.
3. **Relevance Labels**:
   - `DIRECT_SUPPORT`: The document explicitly answers the question.
   - `PARTIAL_SUPPORT`: The document addresses the topic but is incomplete.
   - `NOT_RELEVANT`: The document is topically similar but does not contain the specific evidence requested.
4. **No Evidence Assignment**: Only after reviewing all available candidates, if no document in the reviewed corpus provides sufficient evidence, mark a single row for that case as `NO_EVIDENCE` and leave the rest as `NOT_RELEVANT` or `PENDING`.
5. **Evidence Span**: For `DIRECT_SUPPORT` and `PARTIAL_SUPPORT`, provide an exact contiguous evidence span copied exactly from the frozen document. Do not paraphrase.

## Specific Domain Rules
- **DDI**: Require evidence of the actual interaction (e.g., increases exposure, reduces clearance, contraindicated). A document that merely mentions both drugs is `NOT_RELEVANT`. Note directionality: if A affects B, do not assume B affects A.
- **ADE**: Require evidence that the document connects the drug to the event (e.g., causes, associated with). Recognize negation ("does not increase bleeding", "no association").
- **Pharmacology**: Require the precise mechanistic answer (target, clearance, etc).
- **Medication Safety**: Require direct support for the safety issue (dosing, contraindication).

## High-Risk Cases
For R3 cases (major DDI, contraindications, overdose, severe ADE), require a stronger review standard. At least one direct evidence span must be identified for any positive case.

## Authority
Use actual document metadata. A PubMed article is `PEER_REVIEWED_PUBMED`, not an `FDA_LABEL`.

## Blinding
You are judging evidence, not system performance. You will not see retrieval scores or rankings during annotation.
