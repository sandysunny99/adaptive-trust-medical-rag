# UNSUPPORTED CLAIM HANDLING

- **State Mapping**: `FinalSupportState.UNSUPPORTED` or `INSUFFICIENT_EVIDENCE`.
- **Non-Critical Claims**: If uncritical claims are unsupported, the gate sets `GateDecision.qualify`.
- **Critical Claims**: If a critical claim is unsupported, the gate sets `GateDecision.abstain`.
- **Output Action**: The orchestrator checks `GateDecision`. If `abstain`, it drops the answer and returns a canned abstention message. If `qualify`, it releases the answer (in some implementations it strips unsupported claims, though currently `rag_orchestrator.py` releases `verification.qualified_answer` if present).
