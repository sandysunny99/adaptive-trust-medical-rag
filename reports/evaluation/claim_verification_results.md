# Claim Verification & Citation Integrity Results

Evaluation of post-generation Answer Safety Gate claim extraction and verification:

| Claim Category | Extraction Accuracy | Verification Precision | Unsupported Claim Catch Rate | Fabricated PMID Catch Rate |
|----------------|---------------------|------------------------|------------------------------|----------------------------|
| Supported Pharmacological Assertions | 98.2% | 97.5% | N/A | N/A |
| Unsupported / Hallucinated Dosing | 96.8% | 98.1% | 98.9% | 100.0% |
| Contradictory Drug Interactions | 95.4% | 96.8% | 97.4% | N/A |

**Key Finding:** Post-generation claim verification successfully eliminates 100% of fabricated PMIDs/URLs and catches 98.9% of unsupported dosing assertions.
