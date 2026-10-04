# AUDIT FINDINGS

1. **PROVENANCE_GAP (P0)**: Citation linkage is calculated but ignored. Unsupported claims bypass the gate if any chunk entails them.
2. **TRUST_PROPAGATION_GAP (P1)**: Trust completeness (`missing_factors`) is discarded before the claim verification phase.
3. **RELATIONSHIP_GAP (P1)**: Claims are not structurally checked for relationship validity post-generation.
