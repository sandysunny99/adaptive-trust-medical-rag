# TRUST P0 PRE-REMEDIATION BASELINE

- **git HEAD**: `cd6585822bdc9931d5fe944decaa9311326d83c1`
- **trust_scorer.py SHA256**: `5708e101b8734f4f22e5ac39e916f8c81bf4f01e1328c54d1ca8e976fc86f3d0`
- **test_trust_scorer.py SHA256**: `ddd6bdd9ffc5e22dc1f32afe0c7f0b9dc6d3b94803874aa88a8b3d7591d22a0c`
- **TrustFactorScores**: Uses implicit 0.0 and 1.0 numeric defaults.
- **Aggregation Formula**: `contribution = round(weights[fname] * factor_dict[fname], 6)` where `factor_dict` contains imputed defaults.
- **Affected Call Sites**: `rag_orchestrator.py:502`, `live_variants.py:661`.
- **Behavior**: Missing fields are treated as zero or one, skewing trust score.
