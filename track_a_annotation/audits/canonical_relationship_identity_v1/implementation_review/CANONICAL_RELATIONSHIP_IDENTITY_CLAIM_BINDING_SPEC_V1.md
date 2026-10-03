# Canonical Relationship Identity Claim Binding Specification V1

## 1. Claim Parsing
The `ClaimVerifierV2` will utilize an internal deterministic parser or lightweight extraction to resolve the generated claim into a temporary Canonical structure. 
- *Constraint*: If extraction cannot definitively resolve the subject RxCUI, object RxCUI, predicate, and direction from the claim, it must mark the claim's identity as `AMBIGUOUS`.

## 2. Comparison Logic (Source vs Generated)
1. **Match**:
   `source.subject_rxcui == claim.subject_rxcui` AND
   `source.object_rxcui == claim.object_rxcui` AND
   `source.predicate == claim.predicate` AND
   `source.direction == claim.direction`
2. **Direction Mismatch**: The subject and object are logically reversed.
3. **Entity Mismatch**: Subject or Object RxCUI does not explicitly match.
4. **Predicate Mismatch**: The interaction type conflicts.

## 3. Strict Identity Rule
Fuzzy similarity or NLI-based approximate matching is **prohibited** for satisfying the canonical equality. 
- If the Canonical match passes, the claim proceeds to the NLI check for nuanced text verification.
- If the Canonical match fails (mismatch), it explicitly fails the claim.
- If the Canonical parsing is ambiguous, it is treated as a structural failure, NOT a silent fallback to NLI.

## 4. State Integration
- Mismatch -> `UNSUPPORTED`
- Ambiguous -> `UNSUPPORTED`
- Match -> Proceed to existing NLI semantic entailment.
