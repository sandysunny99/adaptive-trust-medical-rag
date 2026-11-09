# POS02_SOURCE_AUTHORITY_AUDIT_V1

## Amended Source Details
- **Source Identity**: FDA Prescribing Information: Atorvastatin Calcium (FDA Label)
- **Provenance**: `data/evidence/manifest.json` (doc_id: `doc-fda-atorvastatin`)
- **Publication Date**: `2023-04-10`
- **Current Authority Category**: `tier_1_peer_reviewed`
- **Authority Score**: `1.0`

## Audit Findings
The current authority categorization of `tier_1_peer_reviewed` is **semantically incorrect** for this source. An FDA label is a regulatory document with legally binding prescribing information, not an academic paper subjected to journal peer review.

While the authority score of `1.0` is appropriate (FDA labels are the definitive source of truth for pharmacological profiles in this project), the category label should be changed to explicitly reflect its regulatory nature (e.g., `tier_1_regulatory` or similar applicable tag) to maintain rigorous methodological consistency in the research evidence.
