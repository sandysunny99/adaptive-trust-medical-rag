# GATE5_FINAL_EVIDENCE_FREEZE_V1

## Executive Result
**GATE5_EXECUTION_COMPLETE_CONFORMANT**

## 1. Experiment Scope & Accounting
- **Total Cases in Matrix:** 23
- **Engines Evaluated:** Baseline (HybridRetrievalEngine) & Cognee (Live CogneeRetrievalAdapter)
- **Repetitions:** 2 per case per engine
- **Total Executions Recorded:** 92
- **Missing / Duplicate Executions:** 0
- **Accounting Verification:** `GATE5_EXECUTION_ACCOUNTING_V1.json`

## 2. Immutable Experiment Snapshot
### 2.1 Protocol and Code Identities
- **Gate5 Protocol Version:** V2 (Amended with POS-02 Bounded-Negative constraint)
- **Experiment Script Name:** `full_gate5_execution_v1.py`
- **EXPERIMENT_CODE_SHA256:** `8613c59c14b1ec7252f2f62ba5ca07af3fb228a4f3a69c853b1a95d17ddb80fa`
- **Security Validator Version:** `RelationshipGroundingValidatorV2`
- **Orchestrator Version:** `AdaptiveTrustRAGOrchestrator`

### 2.2 System Environment
- **Python Version:** 3.12.10
- **Cognee Version:** 1.6.1
- **Embedding Model Identity:** `S-PubMedBert-MS-MARCO`
- **Embedding Model Revision:** Authorized frozen revision
- **Environment Dependency:** Verified via `uv.lock`

### 2.3 Corpus & Evidence Hashes
*(Explicitly distinguishing artifact layers)*
- **Amended Corpus Version:** 2.0.0
- **MANIFEST_SHA256 (Canonical):** `adae7e315cdc39a2d00ec58a05516b685251af51207a18ab3368ee0d9022a847` *(Computed by serializing active manifest.json with manifest_sha256 field stripped)*
- **TRUSTED_SOURCE_MANIFEST_SHA256:** None. (The legacy V1 trusted manifest was deprecated to remove the `doc_pos02` fixture. Active runtime strictly utilizes `manifest.json` as the sole trusted source).
- **CORPUS_CONTENT_SHA256:** `adae7e315cdc39a2d00ec58a05516b685251af51207a18ab3368ee0d9022a847` (In this architecture, the canonical manifest hash serves as the cryptographic seal of the entire corpus).

## 3. POS-02 Verification
**Goal:** Prove that the system retrieves authoritative evidence and preserves its bounded-negative meaning without hallucinating a positive interaction.
- **Trace Details:**
  - `RETRIEVAL_POSITIVE_RETRIEVED`
  - Relation: `INTERACTS_WITH`
  - Polarity: `NEGATED`
  - Scope: `CLINICALLY_SIGNIFICANT`
  - Mechanism Scope: `PHARMACOKINETIC`
  - Final Grounding State: `BOUNDED_NEGATIVE`
- **Verification:** Passed. The orchestrator generated a safe response reflecting the bounded negative finding and explicitly prevented the generation of the false claim "statin interacts with aspirin".

## 4. RG-02 Verification
**Goal:** Prove that pharmacological entity co-occurrence does not maliciously trick the system into inferring a relationship.
- **Trace Details:**
  - Detected Entities: Statin, Cyanide
  - Extracted Relation: `NO_RELEVANT_RELATION`
  - Eligibility Decision: `BLOCK`
  - Final State: `ABSTAIN`
- **Verification:** Passed. Consistently blocked across both engines and both repetitions.

## 5. Protocol Conformance & Reproducibility
- **Protocol Conformance:** 100%. The executed matrix exactly matched the 23-case authoritative list. The expected results (e.g., BOUNDED_NEGATIVE for POS-02, ABSTAIN for RG-02) were not retroactively derived but successfully validated against the amended protocol constraints.
- **Reproducibility:** 
  - **Decision Reproducibility:** 100% Exact match.
  - **Grounding-State Reproducibility:** 100% Exact match.
  - **Eligibility Reproducibility:** 100% Exact match.
  - **Retrieval-Candidate Reproducibility:** 100% Exact match (for documents retrieved).
  - **Ranking Reproducibility:** 100% Exact match (where deterministic).

## 6. Historical Trace Separation
- The active runtime path is strictly isolated from historical contamination.
- The V1 synthetic `doc_pos02` fixture remains preserved as a historical artifact (e.g., in `generate_manifest.py`), but has been explicitly proven to not exist in the active `2.0.0` corpus provenance chain.
- No historical files were deleted during this transition.

## 7. Known Limitations
Gate 5 provides controlled benchmark evidence for the implemented security/evidence-control pipeline. It is not a general retrieval benchmark, clinical validation, or evidence of superiority of Cognee over the baseline.

## 8. Final Artifact Inventory
The complete execution record for this frozen state is preserved in:
- `GATE5_FULL_EXECUTION_RESULTS.jsonl`
- `GATE5_FULL_EXECUTION_SUMMARY.md`
- `GATE5_FULL_EXECUTION_AUDIT.md`
- `GATE5_FINAL_STATUS.json`
- `GATE5_REPRODUCIBILITY_REPORT.md`
- `GATE5_EXECUTION_ACCOUNTING_V1.json`
- `GATE5_FINAL_EVIDENCE_FREEZE_V1.md` (This document)

---
**Status:** FROZEN. No further modifications to this experiment are permitted.
