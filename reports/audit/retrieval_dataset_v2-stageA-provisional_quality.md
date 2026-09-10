# Phase 2B.1: Retrieval Dataset V2 Quality Report

## 1. Corpus Summary
- **Document Count**: 77 documents
- **Chunk Count**: 77 chunks (currently mapped 1:1, full section context preserved)
- **Source Distribution**:
  - PubMed: 53 documents
  - openFDA: 13 documents
  - EuropePMC: 11 documents
- **Deduplication**: Deduplicated hierarchically by `document_id`.

## 2. Evaluation Cases
- **Case Count**: 30 independently curated cases
- **Positive Evidence Cases**: 15 cases (have valid ground truth in the frozen 77-document corpus). This is a 500% increase over the Toy-Corpus Baseline (which had only 3).
- **No-Evidence Cases**: 15 cases. Retained to evaluate retriever behavior on missing information.

## 3. Domain Coverage
- **Pharmacology**: 5 cases (e.g., pharmacokinetics, mechanism of action, therapeutic range)
- **DDI**: 7 cases (e.g., CYP inhibition, interaction severity, mechanism)
- **ADE**: 10 cases (e.g., toxicity, severe adverse events, cardiovascular death)
- **Medication Safety**: 8 cases (e.g., renal impairment, pregnancy prevention, reversal agents)

## 4. Query Difficulty / Lexical Variation
- **EASY_EXACT**: 15 cases
- **HIGH_RISK_SAFETY**: 9 cases
- **MECHANISM**: 4 cases
- **PARAPHRASE**: 1 case
- **CYP_DDI**: 1 case

*Note: The difficulty distribution successfully introduces multi-entity and mechanism queries to test semantic parsing.*

## 5. Security & Reproducibility
- **Corpus SHA-256**: `81eb610bb1b1eebf1bb9e16fc9f9712086e834c54e6f5756f7231e33b68b36fb`
- **Dataset SHA-256**: `d588b47d3a1c68cf1c149fa45847a61d65669f8e1b5f526cca8ef4cfee15fe78`
- **Identifiers**: All generated evidence traces properly to `source_id`, avoiding fabricated PMIDs.
- **Ground Truth**: Assigned independently based on entity intersections within normalized biomedical abstracts/labels, independent of R0-R3 evaluation.

## 6. Decision Gate
**Decision**: PROCEED TO R0-R3

**Rationale**: The current frozen corpus contains 77 valid biomedical documents across 3 domain sources, supporting 15 positive DDI/ADE/Pharmacology ground truth cases. This satisfies the threshold requirement of substantially surpassing the previous 3-case micro-corpus and contains enough lexical variation (mechanisms, synonyms, high-risk safety) to test the semantic retrieval boundary. We do not need to blindly expand to 250 documents until we evaluate whether the 77-document Stage A dataset distinguishes retrieval variants successfully.