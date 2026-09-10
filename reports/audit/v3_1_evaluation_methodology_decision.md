# Phase 2F.4.1 Evaluation Methodology Decision

## 1. Core Methodological Position
The dataset produced via Candidate-Based AI-Assisted Adjudication (Phase 2F.2 - 2F.4) is officially declared:
**VALID FOR DIAGNOSTIC RETRIEVAL ANALYSIS**
but
**NOT EQUIVALENT TO EXHAUSTIVE INDEPENDENT GROUND TRUTH**

## 2. Separate Evaluation Tracks

### Track A: Diagnostic Evaluation (ALLOWED)
* **Dataset:** AI_ASSISTED_DIAGNOSTIC (The current pilot candidate annotations + false-negative screenings).
* **Purpose:** To identify retrieval behavior, ranking failures, false negatives, candidate coverage, and human adjudication of surfaced evidence.
* **Status:** PERMITTED. 

### Track B: Confirmation Evaluation (LOCKED)
* **Dataset:** Requires a stronger, independently established relevance benchmark. 
* **Purpose:** To definitively confirm generalized clinical retrieval superiority and statistical superiority of F3 over F0.
* **Status:** LOCKED. (Not available yet).

## 3. Dataset Constraints

### Permitted Claims
The current dataset can support observations about:
* Candidate retrieval coverage
* Retrieval failure patterns
* False-positive patterns
* False-negative screening outcomes
* Human adjudication of surfaced evidence

### Prohibited Claims
The current dataset cannot support:
* Definitive F0 vs F3 superiority
* Independent benchmark confirmation
* Generalized clinical retrieval superiority

## 4. Ground Truth Strictures
* The AI-assisted diagnostic labels must **not** be converted into `FINAL_GROUND_TRUTH`. 
* No statistical confirmation of F3 superiority may be claimed from this dataset. 
* The AI-assistance disclosure must remain attached to the dataset.
* The unsampled corpus remainder was not individually reviewed by a human; the dataset cannot establish exhaustive independent ground truth.

## 5. Next Technical Step Directive
A diagnostic comparison of **F0 (BM25 + S-PubMedBERT + Graph + RRF)** vs **F3 (F0 + MedCPT reranking)** may be prepared using the AI-assisted candidate annotations. 
* The resulting report MUST be explicitly titled: **DIAGNOSTIC COMPARISON** (not "Confirmation").
* Diagnostic metrics (candidate recall, candidate coverage, ranking changes, top-k evidence retrieval, false-negative findings) may be evaluated.
* Phase 2G and formal F0/F3 Confirmation Evaluation remain strictly LOCKED.