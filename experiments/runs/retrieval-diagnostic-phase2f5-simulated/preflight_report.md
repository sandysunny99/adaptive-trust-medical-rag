# Stage A: Pre-Flight Diagnostic Report

## 1. Input Verification
- **Corpus Hash:** `e4346ad15ec1f74af9ecc010ef822503eb44638f1020e7f0fcb51ad5c58f42f7` (Match: PASS)
- **Annotation Hash:** `07f1420cfbce67c16c27ae0b3fe478ad4ed6b9d7f04719fe3a63718eb950fdc0` (Match: PASS)
- **V2 Screening Manifest Hash:** `92a2f72e43a5d4b2e7f7645c4e4987b00faf7153e2adc12ae0913e3bafd88e72` (Match: PASS)

## 2. Query Set Verification
- **Expected Queries Present:** PASS (10/10 exact match)

## 3. Configuration Freeze
- **F0:** BM25 + S-PubMedBERT + Graph + RRF
- **F3:** F0 + MedCPT reranking
- **Dataset Label:** AI_ASSISTED_DIAGNOSTIC

## 4. Integrity Guard Status
- **Phase 2F.4 Procedural Integrity:** PASS
- **Ground-Truth Independence:** NOT ESTABLISHED
- **Diagnostic Evaluation:** ALLOWED
- **Confirmation Evaluation:** LOCKED
- **Phase 2G:** LOCKED

## Conclusion
All inputs are frozen and verified. The diagnostic experiment is ready for execution.