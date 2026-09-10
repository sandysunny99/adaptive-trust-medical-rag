# Phase 15 Protocol

## 1. Experimental Unit

One experimental unit is defined as a single **Paired Observation**:
- A specific user query evaluated against a specific corpus state.
- The unit is processed twice: once by the `BASELINE` system, and once by the `HARDENED` system.

## 2. Attack and Scenario Families

| Family | Description |
|--------|-------------|
| **PROMPT_INJECTION** | Malicious queries attempting to override instructions. |
| **RETRIEVAL_POISONING** | Queries triggering candidates with manipulated provenance. |
| **BOUNDARY_VIOLATION** | Valid queries combined with unauthorized LLM-generated action markers. |
| **UNSUPPORTED_CLAIM** | Scenarios designed to induce hallucinations. |
| **CONTRADICTION** | Queries retrieving conflicting authoritative evidence. |
| **BENIGN_CONTROL** | Standard queries with clean evidence. |

## 3. Medical Scope

Focus: Drug-Drug Interactions (DDI), ADE/ADR, PK/PD, dosage contraindications.

## 4. Threats to Validity

The Phase 15 evaluation contains explicit limitations that must be acknowledged:

**Internal Validity:**
- *Stochasticity:* Even at Temperature 0.0, LLM APIs may exhibit minor non-determinism. Paired isolation and random seeds attempt to control this, but edge-case variation is possible.
- *Annotation Subjectivity:* Human adjudicators may disagree on what constitutes an "unnecessary" abstention vs a "useful" abstention. Dual-annotation ($\kappa$) is used to measure and control this bias.

**Construct Validity:**
- *Orchestrator Scope:* The experiment measures `ORCHESTRATOR-LEVEL END-TO-END EVALUATION`. It is not a "production-wide" or "full-system" validation incorporating networking, UI, or clinical deployment environments.

**External Validity:**
- *Generalization:* The 200 cases are curated/synthetic representations of targeted attack families and specific pharmacology domains (e.g., DDI). Effectiveness may not identically generalize beyond this evaluation set to real-world adversarial drift or entirely different medical domains (e.g., surgical procedures).
- *Corpus Representativeness:* The evaluation relies on a specific frozen snapshot of evidence, not a live internet/literature connection.

**Clinical Validity:**
- *Explicit Limitation:* This evaluation measures system security and output grounding adherence. **It does not establish clinical validity or medical safety.** The system remains a research artifact, not an autonomous clinical diagnostic tool.


**Synthetic Dataset Validity Label:**
"The Phase 15 evaluation dataset is a curated synthetic/adversarial benchmark designed to exercise defined security-failure scenarios. It is not claimed to represent the prevalence or distribution of clinical queries in real-world healthcare environments."

**Preview Model External Validity:**
"Phase 15 uses the Gemini 3.1 Pro Preview API model. The evaluation therefore measures the frozen behavior of this specific preview model configuration and should not be interpreted as a general evaluation of all Gemini models or of a permanently stable model release."

**Preview Determinism Limit:**
"temperature=0 and fixed seed are used to reduce stochastic variation; reproducibility remains conditional on the frozen model/API/runtime configuration. If the API does not guarantee perfect seed determinism for the selected endpoint across time, slight execution variations may occur."