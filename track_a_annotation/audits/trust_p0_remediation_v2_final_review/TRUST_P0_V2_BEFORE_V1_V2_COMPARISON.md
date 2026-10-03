# TRUST P0 V2 BEFORE / V1 / V2 COMPARISON

- **ORIGINAL**: Missing data was secretly coerced into `0.0` or `1.0` defaults.
- **V1**: Missing data explicitly `None`, but weight excluded from denominator, allowing incomplete evidence to artificially score highly.
- **V2**: Missing data explicitly `None`, denominator fully retained. Missing required evidence dilutes trust, enforcing safety via abstention.
