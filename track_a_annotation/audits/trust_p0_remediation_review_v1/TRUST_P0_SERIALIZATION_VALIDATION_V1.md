# TRUST P0 SERIALIZATION VALIDATION V1

- `TrustFactorScores.as_dict()` accurately converts the dataclass to a dictionary containing `None`.
- Downstream logging (e.g. `json.dumps` for audit logging) converts `None` to `null` properly. No defaults are reintroduced.
