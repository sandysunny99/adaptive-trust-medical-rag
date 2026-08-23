# Real Execution Pipeline Trace & Runtime Verification

**Execution Status:** `LIVE PIPELINE TRACED & VERIFIED`

## 1. End-to-End Pipeline Execution Path

The live runtime pipeline follows an explicit, un-shortcut execution path from incoming request to verified output:

```
[CLI / HTTP API Request]
         │
         ▼
[adaptive_trust_medical_rag.cli::handle_query] / [api.app::query_endpoint]
         │
         ▼
[adaptive_trust_medical_rag.security.sanitizer::sanitize_query]
  └─ Regex & semantic prompt injection detection
  └─ Zero PHI scrubber & query hash generation
         │
         ▼
[adaptive_trust_medical_rag.trust_scoring.trust_scorer::classify_risk_tier]
  └─ Risk classification: R0, R1, R2, R3
         │
         ▼
[adaptive_trust_medical_rag.retrieval.hybrid_retriever::retrieve_evidence]
  └─ BM25 keyword search
  └─ Dense vector search (pgvector VECTOR(768))
  └─ Graph entity candidate expansion
  └─ Reciprocal Rank Fusion (RRF)
         │
         ▼
[adaptive_trust_medical_rag.trust_scoring.trust_scorer::calculate_trust_score]
  └─ Multi-factor trust scoring: T = w_auth*S_auth + w_fresh*S_fresh + w_ent*S_ent + w_rep*S_rep
         │
         ▼
[Pre-Generation Evidence Eligibility Gate]
  └─ Gating decision: PASS vs ABSTAIN based on risk tier thresholds
     (R0: 0.30, R1: 0.45, R2: 0.60, R3: 0.75)
         │
         ├─── (ABSTAIN) ──► Structured Controlled Abstention Response
         │
         ▼ (PASS)
[Context Construction & Grounded Generation Engine]
  └─ Prompt template assembly with explicit data-only framing
  └─ Generates answer with citation ID linkages
         │
         ▼
[adaptive_trust_medical_rag.claim_verification.claim_verifier::verify_claims]
  └─ Post-Generation Answer Safety Gate
  └─ Claim extraction & NLI evidence cross-referencing
  └─ PMID / URL fabrication check & unverified claim removal
         │
         ▼
[adaptive_trust_medical_rag.audit.audit_logger::log_audit_event]
  └─ Deterministic SHA-256 audit telemetry (Zero PHI)
         │
         ▼
[Verified Final Output]
```

---

## 2. Module Runtime Specification Matrix

| Stage | Python Module | Entry Function / Class | Input Schema | Output Schema | Failure Behavior |
|-------|---------------|------------------------|--------------|---------------|------------------|
| 1. Sanitizer | `security/sanitizer.py` | `sanitize_query()` | `str` | `SanitizationResult` | Rejects query (`rejected=True`) |
| 2. Risk Classification | `trust_scoring/trust_scorer.py` | `classify_risk_tier()` | `str` | `RiskTier` (R0-R3) | Defaults to `R1` |
| 3. Hybrid Retrieval | `retrieval/hybrid_retriever.py` | `retrieve_evidence()` | `query: str, top_k: int` | `list[EvidenceChunk]` | Returns top available chunks |
| 4. Trust Scorer | `trust_scoring/trust_scorer.py` | `calculate_trust_score()` | `EvidenceChunk, RiskTier` | `TrustScoreResult` | Rejects low-score chunks |
| 5. Eligibility Gate | `orchestrator/rag_orchestrator.py` | `evaluate_eligibility()` | `list[TrustScoreResult]` | `GateDecision` | Triggers controlled abstention |
| 6. Generation | `core/pipeline.py` | `generate_answer()` | `query, context_chunks` | `str` | Triggers fallback abstention |
| 7. Claim Verifier | `claim_verification/claim_verifier.py` | `verify_claims()` | `answer, context_chunks` | `ClaimVerificationReport` | Strips unverified claims |
| 8. Audit Log | `audit/audit_logger.py` | `log_audit_event()` | `AuditEvent` | `str` (SHA-256 hash) | Writes JSONL audit record |
