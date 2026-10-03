# TRUST P0 V2 FORMULA VALIDATION

The implementation in `src/adaptive_trust_medical_rag/trust_scoring/trust_scorer.py` precisely matches:
```python
weight_sum = sum(weights[f] for f in TRUST_FACTORS) # Denominator
total = sum(round(weights[fname] * val, 6) for fname in TRUST_FACTORS if val is not None) # Numerator
trust_score = round(total / weight_sum, 4)
```

**Conclusion**: Missing factor contribution is exactly 0 to the numerator, while its weight remains in the denominator.
