# V3.1 Benchmark Quality Report

- **Document Count**: 248
- **Chunk Count**: 248
- **Total Cases**: 75
- **Positive Case Count**: 59
- **No-Evidence Case Count**: 16
- **Average Positives per Case**: ~1.3 (For the 59 positive cases, max 5)

## Domain Distribution
- **Pharmacology**: 19
- **DDI**: 21
- **ADE**: 19
- **Medication Safety**: 16

## Difficulty Distribution
- **MECHANISM**: 19
- **PARAPHRASE**: 16
- **MULTI_ENTITY**: 14
- **CYP_DDI**: 3
- **SYNONYM**: 23

## Risk Tier Distribution
- **R1**: 23
- **R2**: 15
- **R3**: 37

## Hard Negatives
- Integrated into all 59 positive cases to penalize pure lexical matching without semantic coherence.