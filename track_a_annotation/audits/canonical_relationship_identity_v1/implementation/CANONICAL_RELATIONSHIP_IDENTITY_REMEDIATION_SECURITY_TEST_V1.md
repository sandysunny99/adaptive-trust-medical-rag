# Canonical Relationship Identity Security Test Report V1

## Adversarial Scenario Tested

### Direction Reversal Attack
**SOURCE:** Drug A (warfarin, RxCUI 11289) → INHIBITION → Drug B (aspirin, RxCUI 1191), direction A_TO_B
**CLAIM:** Drug B → INHIBITION → Drug A, direction B_TO_A

**Expected:** NLI may score this favorably (both drugs and predicate are textually present in both source and claim). However, the canonical identity check catches the direction reversal.

**Result:** `CanonicalMatchStatus.MISMATCH` with reason "Direction mismatch: source=A_TO_B claim=B_TO_A"

**Outcome:** UNSUPPORTED → AnswerSafetyGate → controlled abstention

### Entity Misattribution
**SOURCE:** warfarin (RxCUI 11289) → INHIBITION → aspirin (RxCUI 1191)
**CLAIM:** metformin (RxCUI 6809) → INHIBITION → aspirin (RxCUI 1191)

**Result:** `CanonicalMatchStatus.MISMATCH` with reason "Subject RxCUI mismatch: source=11289 claim=6809"

### Predicate Substitution
**SOURCE:** warfarin → INHIBITION → aspirin
**CLAIM:** warfarin → INDUCTION → aspirin

**Result:** `CanonicalMatchStatus.MISMATCH` with reason "Predicate mismatch: source=INHIBITION claim=INDUCTION"

### Ambiguity Exploitation
**CLAIM:** Unresolvable drug entity → cannot construct canonical identity → None

**Result:** `CanonicalMatchStatus.UNAVAILABLE` → UNSUPPORTED → controlled failure

## Security Finding Classification
**PLAUSIBLE** — The implementation adds deterministic canonical identity validation for the tested subject, object, predicate, and direction mismatch classes. The control complements semantic NLI rather than replacing it. It reduces a class of entity/predicate/direction mismatch risk.

## What This Does NOT Prove
- Does not prove clinical safety
- Does not prove all hallucinations are prevented
- Does not prove adversarial robustness against all attack classes
- Does not validate the pharmacological correctness of relationships
