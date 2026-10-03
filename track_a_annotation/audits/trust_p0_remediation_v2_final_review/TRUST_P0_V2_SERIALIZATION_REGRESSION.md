# TRUST P0 V2 SERIALIZATION REGRESSION

- `TrustFactorScores.as_dict()` serializes `None` seamlessly.
- JSON conversions (`json.dumps`) correctly output `null`.
- Explicit `0.0` translates to `0.0`. Explicit `1.0` translates to `1.0`.
- No hidden defaults reconstructed during serialization.
