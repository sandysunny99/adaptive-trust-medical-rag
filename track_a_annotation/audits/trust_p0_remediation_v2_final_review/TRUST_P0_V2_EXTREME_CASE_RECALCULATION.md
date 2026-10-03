# TRUST P0 V2 EXTREME CASE RECALCULATION

**Test CASE E (5 factors available, 4 missing for R3)**
- **Available**: `source_authority(0.3)=0.9, query_relevance(0.1)=0.9, entity_match(0.1)=0.9, anti_poisoning(0.01)=0.9, anti_injection(0.01)=0.9`
- **Missing**: `evidence_quality(0.25), freshness(0.1), consistency(0.1), population_match(0.03)`
- **Denominator**: 1.0 (unchanged)
- **Numerator**: (0.3*0.9) + (0.1*0.9) + (0.1*0.9) + (0.01*0.9) + (0.01*0.9) = 0.27 + 0.09 + 0.09 + 0.009 + 0.009 = 0.468
- **Score**: 0.4680. Threshold is 0.75.
- **Result**: Fails R3 gate. Controlled abstention enforced.
