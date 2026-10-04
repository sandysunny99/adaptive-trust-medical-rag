"""Live Medical RAG Service.

Coordinates the real end-to-end medical RAG pipeline for the live web application.
This service is completely decoupled from the frozen research evaluation orchestrator.
It yields SSE events at each stage of execution.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import AsyncGenerator, Any

from adaptive_trust_medical_rag.security.sanitizer import sanitize_query
from adaptive_trust_medical_rag.security_extensions.injection_detector import PromptInjectionDetector
from adaptive_trust_medical_rag.security_extensions.poisoning_detector import RetrievalPoisoningDetector
from adaptive_trust_medical_rag.trust_scoring.trust_scorer import AdaptiveTrustScorer, TrustFactorScores, classify_query_risk
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2, EvidenceChunk, SemanticJudgment, FinalSupportState
from adaptive_trust_medical_rag.verification.canonical_identity import CanonicalRelationshipIdentity, CanonicalDirection, extract_claim_identity, compare_identity

log = logging.getLogger(__name__)


def _ts() -> str:
    from datetime import datetime, UTC
    return datetime.now(UTC).isoformat()


def _sse(event: str, data: dict[str, Any]) -> dict[str, Any]:
    """Helper to return an event tuple."""
    return {"event": event, "data": data}


class LiveMedicalRAGService:
    def __init__(self, app_state: Any) -> None:
        self.app_state = app_state
        self.trust_scorer = AdaptiveTrustScorer()
        self.prompt_detector = PromptInjectionDetector()
        self.poisoning_detector = RetrievalPoisoningDetector()

        # Load prompt template
        import os
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", "LIVE_APP_PROMPT_V1.txt")
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                self.prompt_template = f.read()
        except Exception as e:
            log.warning("Could not load LIVE_APP_PROMPT_V1.txt: %s", e)
            self.prompt_template = ""

    async def execute(
        self,
        request_id: str,
        drug_names: list[str],
        patient_context: dict[str, Any] | None,
        start_time: float,
    ) -> AsyncGenerator[dict[str, Any], None]:
        """Execute the live pipeline and yield SSE event dicts."""
        
        try:
            # ── Stage 1: Input Validation & Sanitization ────────────────────────
            yield _sse("stage_update", {
                "stage": "uploading",
                "status": "running",
                "message": "Sanitizing input...",
                "timestamp": _ts(),
            })

            sanitized_drugs: list[str] = []
            for drug_name in drug_names:
                result = sanitize_query(drug_name)
                if result.rejected:
                    log.warning("Drug name rejected by sanitizer: %s", drug_name[:20])
                    continue
                # Also check prompt injection
                inj_dec = self.prompt_detector.inspect(result.sanitized, request_id)
                if inj_dec.decision.name == "BLOCK":
                    continue
                sanitized_drugs.append(result.sanitized)

            if not sanitized_drugs:
                yield _sse("error", {
                    "code": "NO_VALID_DRUGS",
                    "message": "No valid drug names passed security checks.",
                })
                return

            yield _sse("stage_update", {
                "stage": "uploading",
                "status": "complete",
                "message": f"{len(sanitized_drugs)} drug(s) accepted",
                "timestamp": _ts(),
            })

            # ── Stage 2: Drug Normalization (RxNorm) ─────────────────
            yield _sse("stage_update", {
                "stage": "normalizing",
                "status": "running",
                "message": "Resolving drug entities via RxNorm...",
                "timestamp": _ts(),
            })

            medications = []
            normalizer = getattr(self.app_state, "drug_normalizer", None)
            drug_rxcui_map = {}

            if normalizer:
                try:
                    entities = await normalizer.normalize_batch(sanitized_drugs)
                    for entity in entities:
                        if entity.rxcui:
                            drug_rxcui_map[entity.raw_text.lower()] = entity.rxcui
                            if entity.generic_name:
                                drug_rxcui_map[entity.generic_name.lower()] = entity.rxcui
                                
                        medications.append({
                            "raw_text": entity.raw_text,
                            "canonical_name": entity.generic_name,
                            "rxcui": entity.rxcui,
                            "brand_name": entity.brand_name,
                            "formulation": entity.formulation,
                            "confidence": entity.confidence,
                            "source": entity.source,
                            "status": "MATCHED" if entity.rxcui else "NOT_FOUND",
                        })
                except Exception as e:
                    log.error("RxNorm error: %s", e)
                    for d in sanitized_drugs:
                        medications.append({
                            "raw_text": d,
                            "canonical_name": d.lower(),
                            "status": "UNAVAILABLE",
                        })
            else:
                for d in sanitized_drugs:
                    medications.append({
                        "raw_text": d,
                        "canonical_name": d.lower(),
                        "status": "UNAVAILABLE",
                    })

            yield _sse("rxnorm", {"entities": medications})
            yield _sse("stage_update", {
                "stage": "normalizing",
                "status": "complete",
                "timestamp": _ts(),
            })

            # ── Stage 3: Retrieval ───────────────────────────
            yield _sse("stage_update", {
                "stage": "retrieving",
                "status": "running",
                "message": "Retrieving evidence...",
                "timestamp": _ts(),
            })

            retrieval_engine = getattr(self.app_state, "retrieval_engine", None)
            candidates = []
            evidence_items = []

            if retrieval_engine:
                query_text = " ".join([m.get("canonical_name") or m["raw_text"] for m in medications]) + " drug interactions adverse safety"
                
                # Incorporate patient context into retrieval query
                if patient_context:
                    pc_terms = []
                    if patient_context.get("known_allergies"):
                        pc_terms.extend(patient_context["known_allergies"])
                    if patient_context.get("known_conditions"):
                        pc_terms.extend(patient_context["known_conditions"])
                    if patient_context.get("kidney_impairment") and patient_context["kidney_impairment"] != "none":
                        pc_terms.append(f"kidney impairment {patient_context['kidney_impairment']}")
                    if patient_context.get("liver_impairment") and patient_context["liver_impairment"] != "none":
                        pc_terms.append(f"liver impairment {patient_context['liver_impairment']}")
                    if patient_context.get("pregnancy_status") == "pregnant":
                        pc_terms.append("pregnancy")
                    if patient_context.get("breastfeeding"):
                        pc_terms.append("breastfeeding")
                        
                    if pc_terms:
                        query_text += " " + " ".join(pc_terms)
                        
                drug_names_lower = [m["raw_text"].lower() for m in medications]
                try:
                    # Execute synchronous retrieval (may block event loop in dev, but acceptable for now)
                    candidates = retrieval_engine.retrieve(
                        query=query_text,
                        query_drugs=drug_names_lower,
                        top_k=20
                    )
                except Exception as e:
                    log.error("Retrieval error: %s", e)

            yield _sse("retrieval", {
                "evidence_count": len(candidates),
                "sources": list({c.candidate.metadata.get("source_type", "UNKNOWN") for c in candidates})
            })
            yield _sse("stage_update", {
                "stage": "retrieving",
                "status": "complete",
                "timestamp": _ts(),
            })

            # ── Stage 4: Security (Retrieval Poisoning) ───────────────────────
            yield _sse("stage_update", {
                "stage": "security_checking",
                "status": "running",
                "timestamp": _ts(),
            })
            
            import hashlib
            poisoning_blocked = 0
            safe_candidates = []
            for sc in candidates:
                cand = sc.candidate
                poison_dec = self.poisoning_detector.inspect_provenance(cand.metadata.get("provenance", {}), cand.chunk_id, request_id)
                
                # Check cryptographic provenance hash
                prov = cand.metadata.get("provenance", {})
                expected_hash = prov.get("content_hash")
                actual_hash = hashlib.sha256(cand.text.encode('utf-8')).hexdigest()
                
                if poison_dec.decision.name == "BLOCK" or cand.poisoning_score > 0.4:
                    poisoning_blocked += 1
                elif expected_hash and actual_hash != expected_hash:
                    log.warning("Hash mismatch for %s: expected %s, got %s", cand.chunk_id, expected_hash, actual_hash)
                    poisoning_blocked += 1
                else:
                    safe_candidates.append(sc)

            yield _sse("security", {
                "injection_status": "ALLOW",
                "poisoning_status": "BLOCK" if poisoning_blocked > 0 else "ALLOW",
                "poisoning_reason": f"Blocked {poisoning_blocked} chunks" if poisoning_blocked > 0 else None
            })
            yield _sse("stage_update", {
                "stage": "security_checking",
                "status": "complete",
                "timestamp": _ts(),
            })

            # ── Stage 5: Trust Evaluation ─────────────────────────────
            yield _sse("stage_update", {
                "stage": "trust_evaluating",
                "status": "running",
                "timestamp": _ts(),
            })

            risk_tier = classify_query_risk(" ".join([m["raw_text"] for m in medications]))
            trust_threshold = 0.45
            if risk_tier == "R0": trust_threshold = 0.30
            elif risk_tier == "R2": trust_threshold = 0.60
            elif risk_tier == "R3": trust_threshold = 0.75

            eligible_candidates = []
            max_trust_score = 0.0
            best_factors = None
            
            for sc in safe_candidates:
                cand = sc.candidate
                drug_names_lower = [m["raw_text"].lower() for m in medications]
                entity_match = 1.0 if any(d in cand.text.lower() for d in drug_names_lower) else 0.5
                
                factors = TrustFactorScores(
                    source_authority=cand.source_authority,
                    entity_match=entity_match,
                    freshness=float(cand.metadata.get("freshness_score", 0.8)),
                    consistency=1.0 - cand.poisoning_score,
                    anti_poisoning=1.0 - cand.poisoning_score,
                    anti_injection=1.0,
                )
                
                result = self.trust_scorer.score(
                    chunk_id=cand.chunk_id,
                    risk_class=risk_tier,
                    factors=factors,
                )
                
                # Pre-LLM evidence eligibility
                if result.trust_score >= trust_threshold and cand.source_authority >= 0.3:
                    eligible_candidates.append((sc, result.trust_score, result.missing_factors))
                    
                if result.trust_score > max_trust_score:
                    max_trust_score = result.trust_score
                    best_factors = factors

            yield _sse("trust", {
                "overall_score": max_trust_score,
                "threshold": trust_threshold,
                "risk_class": risk_tier,
                "is_eligible": len(eligible_candidates) > 0,
                "factors": best_factors.__dict__ if best_factors else {},
                "missing_factors": []
            })
            yield _sse("stage_update", {
                "stage": "trust_evaluating",
                "status": "complete",
                "timestamp": _ts(),
            })

            # ── Pre-LLM Controlled Abstention ──────────────────────────
            if not eligible_candidates:
                yield _sse("abstention", {
                    "reason": "Insufficient eligible evidence retrieved to meet trust threshold.",
                    "trust": {
                        "overall_score": max_trust_score,
                        "threshold": trust_threshold,
                        "risk_class": risk_tier,
                    }
                })
                return

            # Format evidence for LLM and Output
            evidence_lines = []
            for i, (sc, ts, missing) in enumerate(eligible_candidates, start=1):
                cand = sc.candidate
                evidence_lines.append(f"[Source {i}]\n{cand.text.strip()}")
                
                evidence_items.append({
                    "chunk_id": cand.chunk_id,
                    "document_id": cand.document_id,
                    "source_type": cand.metadata.get("source_type", "BIOMEDICAL_LITERATURE"),
                    "source_name": cand.source_url or "Retrieved",
                    "title": f"Evidence [Source {i}]",
                    "text": cand.text,
                    "source_authority": cand.source_authority,
                    "trust_score": ts,
                    "freshness": float(cand.metadata.get("freshness_score", 0.8)),
                    "retrieval_method": "hybrid-rrf",
                    "provenance_status": "RETRIEVED"
                })

            evidence_block = "\n\n".join(evidence_lines)

            # ── Stage 6: LLM Generation ─────────────────────────────
            yield _sse("stage_update", {
                "stage": "generating",
                "status": "running",
                "timestamp": _ts(),
            })

            query_str = ", ".join([m["raw_text"] for m in medications])
            patient_ctx_str = json.dumps(patient_context) if patient_context else "None provided."
            
            prompt = self.prompt_template.format(
                query=query_str,
                patient_context=patient_ctx_str,
                risk_tier=risk_tier,
                evidence_block=evidence_block
            )

            llm_backend = getattr(self.app_state, "llm_backend", None)
            structured_result = None
            
            if not llm_backend:
                yield _sse("error", {
                    "code": "PROVIDER_CONFIGURATION_REQUIRED",
                    "message": "LLM Provider is not configured or unavailable."
                })
                yield _sse("stage_update", {
                    "stage": "error",
                    "status": "complete",
                    "timestamp": _ts()
                })
                return

            try:
                # Use JSON output mode for the provider
                gen_result = await llm_backend.generate_structured(prompt, {"type": "json_object"})
                raw_text = gen_result.content
                
                try:
                    structured_result = json.loads(raw_text)
                except json.JSONDecodeError:
                    log.error("LLM Output Validation Failure: output is not valid JSON")
                    yield _sse("error", {"code": "LLM_OUTPUT_VALIDATION_FAILURE", "message": "Failed to parse LLM structured output."})
                    return
                    
            except Exception as e:
                log.error("LLM Generation failed: %s", e)
                yield _sse("error", {"code": "LLM_ERROR", "message": str(e)})
                return

            yield _sse("stage_update", {
                "stage": "generating",
                "status": "complete",
                "timestamp": _ts(),
            })

            # ── Stage 7: Claim Verification & Answer Safety Gate ────────
            yield _sse("stage_update", {
                "stage": "claim_verifying",
                "status": "running",
                "timestamp": _ts(),
            })

            claims_made = structured_result.get("claims_for_verification", [])
            claims_out = []
            
            # Very basic claim verification since the full VerificationReport requires EvidenceChunks
            verifier = getattr(self.app_state, "claim_verifier", None)
            all_supported = True
            
            if verifier and claims_made:
                evidence_chunk_objs = []
                for i, (sc, ts, missing) in enumerate(eligible_candidates, start=1):
                    evidence_chunk_objs.append(EvidenceChunk(
                        chunk_id=sc.candidate.chunk_id,
                        text=sc.candidate.text,
                        source_authority=sc.candidate.source_authority,
                        citation_index=i,
                        trust_score=ts,
                        missing_factors=missing,
                    ))
                    
                for cid, claim_text in enumerate(claims_made):
                    try:
                        # ClaimVerifierV2 expects a single string answer, but we have structured JSON.
                        # We can verify each claim individually as an "answer".
                        v_report = verifier.verify(claim_text, evidence_chunk_objs, risk_tier=risk_tier, drug_rxcui_map=drug_rxcui_map)
                        
                        support_state = "UNSUPPORTED"
                        if v_report.decision.name == "qualify" or v_report.decision.name == "release":
                            support_state = "SUPPORTED"
                        else:
                            all_supported = False
                            
                        claims_out.append({
                            "claim_id": cid,
                            "text": claim_text,
                            "support_state": support_state,
                            "citation_present": True,
                            "entailment": v_report.grounding_ratio,
                            "canonical_identity_status": None,
                        })
                    except Exception as e:
                        log.error("Claim verification error: %s", e)
                        
            yield _sse("stage_update", {
                "stage": "claim_verifying",
                "status": "complete",
                "timestamp": _ts(),
            })
            
            # Post-LLM Safety Gate
            yield _sse("stage_update", {
                "stage": "safety_gating",
                "status": "running",
                "timestamp": _ts(),
            })
            
            gate_decision = "release"
            abstention_reason = None
            
            if not all_supported:
                gate_decision = "abstain"
                abstention_reason = "One or more generated claims failed post-generation verification."
                
                # Overwrite structured_result for abstention
                yield _sse("abstention", {
                    "reason": abstention_reason,
                    "trust": {
                        "overall_score": max_trust_score,
                        "threshold": trust_threshold,
                        "risk_class": risk_tier,
                    }
                })
                return

            yield _sse("stage_update", {
                "stage": "safety_gating",
                "status": "complete",
                "timestamp": _ts(),
            })

            # Format Response
            elapsed = round((time.time() - start_time) * 1000, 1)
            
            provenance = []
            for ec in evidence_items:
                provenance.append({
                    "level": "evidence",
                    "id": ec["chunk_id"],
                    "label": ec["title"],
                    "detail": ec["text"][:100] + "..."
                })

            response_data = {
                "request_id": request_id,
                "input_mode": "direct_drugs",
                "processing_time_ms": elapsed,
                "medications": medications,
                "patient_context_used": patient_context,
                "interactions": structured_result.get("interactions", []),
                "adverse_reactions": structured_result.get("adverse_reactions", []),
                "warnings": structured_result.get("warnings", []),
                "food_guidance": structured_result.get("food_guidance", []),
                "patient_considerations": structured_result.get("patient_considerations", []),
                "trust": {
                    "overall_score": max_trust_score,
                    "threshold": trust_threshold,
                    "risk_class": risk_tier,
                    "is_eligible": True,
                    "factors": best_factors.__dict__ if best_factors else {},
                    "missing_factors": []
                },
                "security": {
                    "injection_status": "ALLOW",
                    "poisoning_status": "BLOCK" if poisoning_blocked > 0 else "ALLOW",
                    "poisoning_reason": f"Blocked {poisoning_blocked} chunks" if poisoning_blocked > 0 else None
                },
                "claims": claims_out,
                "evidence": evidence_items,
                "provenance": provenance,
                "conclusion": structured_result.get("conclusion", ""),
                "gate_decision": gate_decision,
                "abstention_reason": abstention_reason,
            }

            yield _sse("answer", response_data)

            yield _sse("complete", {
                "request_id": request_id,
                "duration_ms": elapsed,
            })

        except Exception as e:
            log.error("Pipeline error for %s: %s", request_id, e)
            import traceback
            traceback.print_exc()
            yield _sse("error", {
                "code": "PIPELINE_ERROR",
                "message": str(e),
            })
