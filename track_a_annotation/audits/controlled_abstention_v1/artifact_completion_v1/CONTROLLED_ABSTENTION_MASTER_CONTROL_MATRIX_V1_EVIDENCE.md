# MASTER CONTROL MATRIX - EVIDENCE BASED

| Condition | Specified | Implemented | Connected | Tested | Observed | Final Gate | Abstention | Fail Behavior | Evidence Reference | Validation Boundary | Finding |
|---|---|---|---|---|---|---|---|---|---|---|---|
| No evidence | YES | YES | YES | YES | YES | `passed=False` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_02)` | Pre-Gen Gate | - |
| Insufficient evidence | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_04)` | Post-Gen Gate | - |
| Low trust | YES | YES | YES | YES | YES | `passed=False` | YES | FAIL CLOSED | Code logic (AdaptiveTrustScorer) | Pre-Gen Gate | - |
| Missing trust | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_08)` | Post-Gen Gate | - |
| R3 failure | YES | YES | YES | UNKNOWN | UNKNOWN | `passed=False` | YES | FAIL CLOSED | Code logic | Pre-Gen Gate | Not specifically tested offline |
| Unsupported claim | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_05)` | Post-Gen Gate | - |
| Invalid citation | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_06)` | Post-Gen Gate | - |
| Missing citation | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | Code logic (ClaimVerifierV2) | Post-Gen Gate | - |
| Contradiction | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_14)` | Post-Gen Gate | - |
| Unsupported relationship | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_12)` | Post-Gen Gate | - |
| NO_RELEVANT_RELATION | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_13)` | Post-Gen Gate | Identity gap exists |
| Provenance failure | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_06)` | Post-Gen Gate | - |
| Ambiguity | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_16)` | Post-Gen Gate | - |
| Mixed claims | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_17)` | Post-Gen Gate | Blocks entire answer |
| Mixed evidence | YES | YES | YES | YES | YES | `GateDecision.abstain` | YES | FAIL CLOSED | `scratch/test_abstention_v2.py (CASE_07)` | Post-Gen Gate | - |
| Reason traceability | YES | YES | YES | YES | YES | `RAGResponse` | YES | FAIL CLOSED | Output inspection | Orchestrator Return | - |
| Verifier failure | YES | YES | YES | YES | YES | `RAGResponse` | YES | FAIL CLOSED | Code logic | Post-Gen Gate | Raises exception -> caught by pipeline |
