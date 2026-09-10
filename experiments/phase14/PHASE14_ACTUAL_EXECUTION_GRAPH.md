# Phase 14 Actual Execution Graph

Traced from [`rag_orchestrator.py`](file:///c:/Users/sunny/Downloads/CASE%20STUDY/src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py)

```text
RAGRequest (User Query)
       │
       ▼
AdaptiveTrustRAGOrchestrator.query()
       │
       ├─── Step 1.5: PromptInjectionDetector.inspect(raw_query, request_id)
       │         Input:  raw user query (pre-sanitization)
       │         Output: SecurityDecision (ALLOW / BLOCK / FLAG)
       │         Fail:   BLOCK → _abstain() [retrieval.call_count = 0, llm.call_count = 0]
       │
       ├─── Step 1: sanitize_query(raw_query)
       │         Input:  raw query
       │         Output: SanitizationResult (sanitized text, rejected flag)
       │         Fail:   rejected = True → _abstain()
       │
       ├─── Step 2: Drug Entity Normalization
       │         Input:  sanitized query
       │         Output: list[str] drug names (RxNorm-resolved or suffix-matched)
       │
       ├─── Step 3: classify_query_risk(sanitized_query) → R0/R1/R2/R3
       │
       ├─── Step 4: HybridRetrievalEngine.retrieve(query, drugs, top_k)
       │         Output: list[ScoredCandidate] (BM25 + Vector + Graph + RRF)
       │
       ├─── Step 4.5: RetrievalPoisoningDetector.inspect_provenance() [LOOP]
       │         Input:  each candidate's .metadata["provenance"]
       │         Output: SecurityDecision per candidate (ALLOW / BLOCK)
       │         Effect: retrieval_security_states dict populated
       │
       ├─── Step 5: AdaptiveTrustScorer.score() [LOOP]
       │         Input:  TrustFactorScores per candidate
       │         Output: trust_score per chunk_id
       │
       ├─── Step 6: EvidenceEligibilityGate.evaluate()  ← GATE 1
       │         Input:  candidates, risk_tier, trust_scores, security_states
       │         Output: EvidenceEligibilityResult (eligible_chunks, rejected_ids)
       │         Fail:   insufficient eligible → _abstain()
       │         Effect: poisoned/low-trust/low-authority chunks EXCLUDED
       │
       ├─── Step 7: LLM.generate(grounded_prompt)
       │         Input:  build_grounded_prompt(query, risk_tier, eligible_candidates)
       │         Output: raw_answer string
       │
       ├─── Step 7.5: Output Classification (Claim vs Action)
       │         │
       │         ├── parse_action_request(raw_answer)
       │         │     ├── ActionParseError → _abstain() [FAIL-CLOSED]
       │         │     ├── None → normal claim path (Step 8)
       │         │     └── AgentActionRequest → authorization path
       │         │
       │         └── [ACTION PATH]
       │               ├── AuthorizationBoundary.authorize(domain, action, principal)
       │               │     ├── UNAUTHORIZED → _abstain() [tool_executor.execution_count = 0]
       │               │     └── ALLOW → ToolExecutor.execute(action_request)
       │               └── Return RAGResponse(tool_executed)
       │
       ├─── Step 8: AnswerSafetyGate.verify(raw_answer, evidence_chunks)  ← GATE 2
       │         Substages:
       │           1. decompose_into_claims()
       │           2. align_claims_to_evidence()
       │           3. citation integrity check
       │           4. detect_contradictions()
       │           5. confidence computation
       │         Output: VerificationReport (release / qualify / abstain)
       │         Fail:   abstain → _abstain()
       │
       └─── Step 9: Final Answer Formatting
                 ├── release → raw_answer + RESEARCH_DISCLAIMER
                 ├── qualify → qualified_answer + RESEARCH_DISCLAIMER
                 └── Return RAGResponse
```

## Security Checkpoint Summary

| Step | Component | Fail Behavior | Data Entering | Data Leaving |
|------|-----------|---------------|---------------|--------------|
| 1.5 | PromptInjectionDetector | Fail-closed: abstain | Raw query | SecurityDecision |
| 4.5 | RetrievalPoisoningDetector | Fail-closed: exclude | Provenance metadata | SecurityDecision |
| 6 | EvidenceEligibilityGate | Fail-closed: abstain | Candidates + trust + security | Eligible chunks only |
| 7.5 | ActionParser + AuthorizationBoundary | Fail-closed: abstain | LLM output | AgentActionRequest or None |
| 8 | AnswerSafetyGate | Fail-closed: abstain | LLM answer + evidence | VerificationReport |