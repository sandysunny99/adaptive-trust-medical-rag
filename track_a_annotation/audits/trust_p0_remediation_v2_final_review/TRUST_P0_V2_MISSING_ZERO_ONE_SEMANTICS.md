# TRUST P0 V2 MISSING VS EXPLICIT ZERO/ONE SEMANTICS

- **Missing vs Explicit Zero**: Both contribute `0.0` to the numerator (identical numerical score impact), but `Missing` explicitly populates the `missing_factors` audit list, whereas `Explicit Zero` does not. Downstream systems can differentiate via metadata.
- **Missing vs Explicit One**: `Explicit One` contributes its full weight to the numerator. `Missing` contributes zero. They are distinguishable mathematically and semantically.
