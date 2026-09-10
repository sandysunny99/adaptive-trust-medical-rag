# Phase 15 Dataset Validation Report

**Date:** 2026-09-08
**Validator:** `scratch/phase15_dataset_validator.py`

## Structural Validation Results

| Check | Result |
|-------|--------|
| N = 200 | PASS |
| PROMPT_INJECTION = 35 | PASS |
| RETRIEVAL_POISONING = 35 | PASS |
| BOUNDARY_VIOLATION = 35 | PASS |
| UNSUPPORTED_CLAIM = 35 | PASS |
| CONTRADICTION = 30 | PASS |
| BENIGN_CONTROL = 30 | PASS |
| All 200 case IDs unique | PASS |
| All 200 queries unique | PASS |
| No prohibited placeholders | PASS |
| All required schema fields | PASS |
| All provenance fields valid | PASS |
| All expected_security_property | PASS |
| PI: adversarial_payload present | PASS |
| RP: evidence_fixture present | PASS |
| BV: principal + action present | PASS |
| CT: evidence_a + evidence_b | PASS |
| No near-duplicate prefixes | PASS |

## Diversity Metrics

| Metric | Value |
|--------|-------|
| Distinct drug entities | 65 |
| Distinct attack subtypes | 171 |
| Task categories | 9 (DDI: 52, medication_safety: 65, ADR: 31, MOA: 18, PK: 18, pharmacokinetics: 9, contraindication: 3, toxicology: 3, PD: 1) |
| Unique queries | 200/200 |
| Synthetic/adversarial provenance | 200/200 |

## Provenance Breakdown

All 200 cases are labeled `SYNTHETIC_ADVERSARIAL_FIXTURE` or `SYNTHETIC_BENCHMARK_QUERY`. No case claims to represent real clinical data or to originate from a real external source (PubMed, FDA, etc.).

## Near-Duplicate Analysis

No near-duplicate query prefixes (first 50 characters) were detected. The 200 cases represent 200 genuinely differentiated experimental stimuli.

## Medical Content Notes

- Drug entities span multiple pharmacological classes: anticoagulants, antiplatelets, statins, ACE inhibitors, ARBs, beta-blockers, calcium channel blockers, antibiotics, antifungals, NSAIDs, opioids, antidepressants, antipsychotics, anticonvulsants, immunosuppressants, and more.
- Task categories exercise real pharmacological reasoning: drug-drug interactions, adverse drug reactions, contraindications, pharmacokinetics, and medication safety.
- Adversarial payloads include distinct attack subtypes: instruction override, system prompt impersonation, delimiter injection, role manipulation, tool-use coercion, authority impersonation, and many others.

## Dataset SHA-256

```
af71c70d36081b1b68316b5ff8636969c8b964c9655f752b41112694ebc02c48
```

## Zero Model Calls

**Confirmed:** Zero API/model generation calls were made during dataset construction or validation.

## Validation Status

**DATASET VALIDATION: PASS**
