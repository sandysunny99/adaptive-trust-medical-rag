import sys
import re
from pathlib import Path

p = Path('src/adaptive_trust_medical_rag/orchestrator/rag_orchestrator.py')
content = p.read_text(encoding='utf-8')

query_method_regex = re.compile(
    r'(def query\(self, request: RAGRequest\) -> RAGResponse:.*?)(    # ── Internal helpers ──)',
    re.DOTALL
)

new_query_method = '''def query(self, request: RAGRequest) -> RAGResponse:
        """
        Execute the end-to-end Adaptive Trust-Aware RAG pipeline.
        """
        import uuid
        session_id = request.session_id or f"sess_{uuid.uuid4().hex[:8]}"
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        
        security_context = SecurityContext(
            request_id=request_id,
            session_id=session_id,
            principal="USER"
        )
        
        audit: list[dict[str, Any]] = []

        def _log(step: str, detail: dict) -> None:
            audit.append({"step": step, "detail": detail})

        _log("session_start", {"session_id": session_id, "query": request.query})

        # Phase 14: Step 1.5 - Prompt Injection Detection (BEFORE processing)
        # Using simple query, not yet sanitized, for injection detection
        injection_decision = self._prompt_detector.inspect(request.query, request_id)
        security_context.injection_status = injection_decision
        security_context.add_decision(injection_decision)
        _log("prompt_injection_detection", {"decision": injection_decision.decision.value, "reason": injection_decision.reason_code})
        
        if injection_decision.decision == SecurityState.BLOCK:
            return self._abstain(
                session_id=session_id,
                query_hash=hashlib.sha256(request.query.encode()).hexdigest(),
                risk_tier="R3",  # default high risk for malicious requests
                reason="Query blocked due to security policy (Prompt Injection).",
                audit=audit,
                security_context=security_context
            )

        # 🚀 Step 1: Input sanitization
        sanitization_result = sanitize_query(request.query)
        sanitized_query = sanitization_result.sanitized

        query_hash = hashlib.sha256(sanitized_query.encode()).hexdigest()
        _log("sanitization", {"query_hash": query_hash})

        if sanitization_result.rejected:
            # Re-evaluate with injection detector explicitly logging block
            return self._abstain(
                session_id=session_id,
                query_hash=query_hash,
                risk_tier="R0",
                reason="Query rejected by security sanitizer.",
                audit=audit,
                security_context=security_context
            )

        # 🚀 Step 2: Drug entity normalization
        if self._drug_normalizer:
            query_drugs = self._drug_normalizer.normalize(sanitized_query)
        else:
            query_drugs = self._extract_drugs_simple(sanitized_query)
        _log("entity_normalization", {"drugs": query_drugs})

        # 🚀 Step 3: Query risk classification
        if request.risk_tier_override:
            risk_tier = request.risk_tier_override
        else:
            risk_tier = classify_query_risk(sanitized_query)

        _log("risk_classification", {"risk_tier": risk_tier})

        # 🚀 Step 4: Hybrid retrieval
        candidates = self._retrieval.retrieve(
            query=sanitized_query,
            query_drugs=query_drugs,
            top_k=request.top_k,
        )

        _log(
            "retrieval",
            {
                "candidate_count": len(candidates),
                "chunk_ids": [sc.candidate.chunk_id for sc in candidates],
            },
        )
        
        # Phase 14: Step 4.5 - Retrieval Poisoning Detection
        retrieval_security_states = {}
        for sc in candidates:
            cand = sc.candidate
            poison_dec = self._poisoning_detector.inspect_provenance(cand.metadata.get("provenance", {}), cand.chunk_id, request_id)
            retrieval_security_states[cand.chunk_id] = poison_dec
            security_context.add_decision(poison_dec)
        security_context.retrieval_security_states = retrieval_security_states

        # 🚀 Step 5: Adaptive trust scoring
        trust_scores: dict[str, float] = {}
        for sc in candidates:
            cand = sc.candidate
            entity_match = 1.0 if any(d in cand.text.lower() for d in query_drugs) else 0.5
            factors = TrustFactorScores(
                source_authority=cand.source_authority,
                entity_match=entity_match,
                freshness=float(cand.metadata.get("freshness_score", 0.8)),
                consistency=1.0 - cand.poisoning_score,
                anti_poisoning=1.0 - cand.poisoning_score,
                anti_injection=1.0 - cand.poisoning_score,
            )
            result = self._trust_scorer.score(
                chunk_id=cand.chunk_id,
                risk_class=risk_tier,
                factors=factors,
            )
            trust_scores[cand.chunk_id] = result.trust_score

        _log(
            "trust_scoring",
            {
                "scores": {cid: round(s, 4) for cid, s in trust_scores.items()},
            },
        )

        # 🚀 Step 6: Evidence eligibility gate (pre-generation)
        eligibility = self._eligibility_gate.evaluate(candidates, risk_tier, trust_scores, retrieval_security_states)

        _log(
            "evidence_eligibility_gate",
            {
                "passed": eligibility.passed,
                "eligible_count": len(eligibility.eligible_chunks),
                "rejected_ids": eligibility.rejected_chunk_ids,
                "reason": eligibility.reason,
            },
        )

        if not eligibility.passed:
            return self._abstain(
                session_id=session_id,
                query_hash=query_hash,
                risk_tier=risk_tier,
                reason=eligibility.reason or "Evidence eligibility gate failed.",
                audit=audit,
                security_context=security_context
            )

        eligible_candidates = eligibility.eligible_chunks

        # Phase 14: Step 6.5 - Authorization Boundary check for READ_DATA EVIDENCE
        auth_decision = self._auth_boundary.authorize(EntityDomain.EVIDENCE, ActionType.READ_DATA, request_id, security_context.principal)
        security_context.authorization_states.append(auth_decision)
        security_context.add_decision(auth_decision)
        _log("authorization_boundary", {"decision": auth_decision.decision.value, "reason": auth_decision.reason_code})
        
        if auth_decision.decision == SecurityState.UNAUTHORIZED_ACTION_REJECTED:
            return self._abstain(
                session_id=session_id,
                query_hash=query_hash,
                risk_tier=risk_tier,
                reason="Authorization Boundary Blocked Action: READ_DATA on EVIDENCE.",
                audit=audit,
                security_context=security_context
            )

        # 🚀 Step 7: Grounded LLM generation
        prompt = build_grounded_prompt(sanitized_query, risk_tier, eligible_candidates)
        raw_answer = self._llm.generate(prompt)

        _log("llm_generation", {"prompt_length": len(prompt), "answer_length": len(raw_answer)})

        # 🚀 Step 8: Answer safety gate (post-generation)
        evidence_chunks = [
            EvidenceChunk(
                chunk_id=sc.candidate.chunk_id,
                text=sc.candidate.text,
                source_authority=sc.candidate.source_authority,
                citation_index=i,
            )
            for i, sc in enumerate(eligible_candidates, start=1)
        ]

        safety_gate = AnswerSafetyGate(risk_tier=risk_tier)
        verification = safety_gate.verify(raw_answer, evidence_chunks)

        _log(
            "answer_safety_gate",
            {
                "decision": verification.decision.value,
                "confidence": verification.confidence,
                "grounding_ratio": verification.grounding_ratio,
                "contradiction_score": verification.contradiction_score,
                "explanation": verification.explanation,
            },
        )

        # 🚀 Step 9: Final answer formatting

        if verification.decision == GateDecision.abstain:
            return self._abstain(
                session_id=session_id,
                query_hash=query_hash,
                risk_tier=risk_tier,
                reason=verification.explanation,
                audit=audit,
                verification=verification,
                trust_scores=list(trust_scores.values()),
                chunk_ids=[sc.candidate.chunk_id for sc in eligible_candidates],
                security_context=security_context
            )

        final_answer = (
            verification.qualified_answer
            if verification.decision == GateDecision.qualify and verification.qualified_answer
            else raw_answer
        ) + RESEARCH_DISCLAIMER

        status = (
            PipelineStatus.qualified
            if verification.decision == GateDecision.qualify
            else PipelineStatus.released
        )

        return RAGResponse(
            session_id=session_id,
            query_hash=query_hash,
            risk_tier=risk_tier,
            status=status,
            answer=final_answer,
            confidence=verification.confidence,
            trust_scores=list(trust_scores.values()),
            retrieved_chunk_ids=[sc.candidate.chunk_id for sc in eligible_candidates],
            gate_decision=verification.decision.value,
            verification_report=verification,
            audit_log=audit,
            security_events=security_context.cumulative_decisions
        )

'''

content = query_method_regex.sub(new_query_method + r'\n\n\2', content)

abstain_regex = re.compile(
    r'(def _abstain\(.*?\n        chunk_ids: list\[str\] \| None = None,\n    \) -> RAGResponse:.*?)(\n        threshold = EvidenceEligibilityGate)',
    re.DOTALL
)
content = abstain_regex.sub(r'\1        security_context: SecurityContext | None = None,\n    ) -> RAGResponse:\2', content)

abstain_body_regex = re.compile(
    r'(verification_report=verification,\n            audit_log=audit,\n        \))',
    re.DOTALL
)
content = abstain_body_regex.sub(r'verification_report=verification,\n            audit_log=audit,\n            security_events=security_context.cumulative_decisions if security_context else []\n        )', content)


p.write_text(content, encoding='utf-8')
