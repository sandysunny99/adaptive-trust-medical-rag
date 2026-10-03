# P1 RELATIONSHIP ADVERSARIAL TEST
- **Test**: Claim cites Source 1. Source 1 textually entails claim, but its `relationship_scope` is `NO_RELEVANT_RELATION`.
- **Result**: The verifier correctly forces `UNSUPPORTED`. The pre-generation block semantics are fully preserved at the post-generation gate.
