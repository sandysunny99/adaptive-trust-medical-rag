# TRUST MISSING DATA POLICY SOURCE MATRIX V1

| Source File | Section | Exact Rule / Mention | Counterpart in Implementation | Normative/Descriptive |
|---|---|---|---|---|
| `AGENTS.md` | Absolute Safety & Grounding Directives | "When evidence is missing... the system **must abstain** using the standard structured abstention template." | `rag_orchestrator.py` threshold check | Normative |
| `AGENTS.md` | Core Stance | "Every factual medical claim must be grounded in retrieved, verifiable evidence. Abstention is a correct, valid, and expected outcome when evidence is insufficient or contradictory." | ClaimVerifierV2, RAG abstention logic | Normative |
| `medical-safety.md` | Controlled Abstention Gate | "The system must refuse to speculate when: Trust score is below the risk class threshold (R0: 0.30, R1: 0.45, R2: 0.60, R3: 0.75)." | `AdaptiveTrustScorer.score` | Normative |
| `medical-safety.md` | Controlled Abstention Gate | "Query involves High-Risk (R3) scenarios... without verified high-authority evidence." | `rag_orchestrator.py` authority threshold | Normative |
| `rag-integrity.md` | Citation Integrity | "If a generated claim cannot be verified against the session evidence, it must be stripped or the answer rejected." | `ClaimVerifierV2` | Normative |
