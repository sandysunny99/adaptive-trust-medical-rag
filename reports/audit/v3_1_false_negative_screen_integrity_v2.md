# Phase 2F.4 V2 False-Negative Screen Integrity Report

This document reports the integrity audit for the Candidate-Based Human Adjudication (V2) protocol.

## Integrity Checklist

| Requirement | Status | Note |
|-------------|--------|------|
| 1. V2 sampling is reproducible | PASS | Cryptographic SHA256 deterministic seeds verified. |
| 2. Recorded corpus hash matches | PASS | `e4346ad15ec1f74af9ecc010ef822503eb44638f1020e7f0fcb51ad5c58f42f7` |
| 3. All escalations adjudicated | PASS | All 8 escalations have received human explicit decisions. |
| 4. No automated human labels | PASS | Screening only provided triage categories. |
| 5. No bulk-labeling of remainder | PASS | The unsampled 95% remainder remains strictly UNSURFACED_REMAINDER. |
| 6. V1/V2 Separation | PASS | V1 and V2 artifacts are isolated into separate directories. |
| 7. AI-Assisted Disclosure | PASS | Process explicitly documented as AI-assisted human annotation. |

## Metadata Summary
- **Protocol Version:** V3.1-FN-SCREEN-V2
- **Corpus Hash:** e4346ad15ec1f74af9ecc010ef822503eb44638f1020e7f0fcb51ad5c58f42f7
- **Sampling Method:** SHA256(case_id) at 5.0% rate.
- **Total Escalations:** 8
- **New Evidence Discovered:** NONE IDENTIFIED

## Conclusion
The V2 Candidate-Based False-Negative Screening protocol executed correctly according to the strict guidelines, successfully addressing the V1 reproducibility flaw.
