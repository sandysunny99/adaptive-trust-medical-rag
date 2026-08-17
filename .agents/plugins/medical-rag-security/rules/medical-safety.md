---
name: medical-safety-rules
description: Medical domain safety rules, clinical disclaimers, entity grounding, and controlled abstention requirements.
trigger: always_on
---

# Medical Domain Safety Rules

## 1. Non-Clinical Use Disclaimer
- This software is a research testbed and not an FDA-approved/certified medical diagnostic or decision-making system.
- Every response must communicate that it is an evidence-grounded research output, not clinical advice.

## 2. Drug Entity Grounding & Attribution
- Pharmacological assertions (dosing, interactions, ADEs, contraindications) must accurately match the normalized RxNorm entity (RxCUI / generic name).
- Never attribute findings from a related compound or different salt/ester form unless explicitly stated in the evidence.
- Population constraints (e.g., pediatric, geriatric, pregnancy category, renal impairment) must be strictly preserved.

## 3. Controlled Abstention Gate
- The system must refuse to speculate when:
  - Trust score is below the risk class threshold (R0: 0.30, R1: 0.45, R2: 0.60, R3: 0.75).
  - Unresolved critical contradictions exist between retrieved sources of equal authority.
  - Query involves High-Risk (R3) scenarios (e.g., lethal dosage, severe drug-drug contraindications) without verified high-authority evidence.
