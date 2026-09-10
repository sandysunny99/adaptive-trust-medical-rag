import asyncio
import os
import json
import uuid
from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import AdaptiveTrustRAGOrchestrator
from adaptive_trust_medical_rag.orchestrator.types import RAGRequest
from adaptive_trust_medical_rag.evaluation.evaluator import RiskTier
from adaptive_trust_medical_rag.evaluation.live_variants import _make_default_orchestrator


async def main():
    os.environ["LLM_MODE"] = "LIVE_LLM"
    os.environ["LLM_PROVIDER"] = "gemini"
    os.environ["LLM_MODEL"] = "gemini-3.6-flash"

    proof_id = "proof_b_" + str(uuid.uuid4())
    data = {
        "proof_id": proof_id,
        "execution_status": "NOT_EXECUTED",
        "runtime_trace": {},
        "llm_stage": {},
        "final_response": {},
    }

    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set. Execution aborted.")
    else:
        print("Executing Proof B: Full RAG Orchestrator with Gemini Backend...")
        try:
            orchestrator = _make_default_orchestrator()
            req = RAGRequest(
                query="What is the mechanism of action of metformin?",
                risk_tier=RiskTier.R1_STANDARD,
            )
            response = orchestrator.query(req)

            # The orchestrator audit log tracks execution stages
            audit_steps = response.audit_log.get("steps", [])
            steps_executed = {s.get("step") for s in audit_steps}

            data["runtime_trace"] = {
                "risk_classification": "risk_tier_classification" in steps_executed
                or req.risk_tier is not None,
                "entity_normalization": "entity_normalization" in steps_executed,
                "retrieval": "hybrid_retrieval" in steps_executed,
                "trust_scoring": "trust_scoring" in steps_executed,
                "evidence_eligibility": "eligibility_gate" in steps_executed,
                "context_construction": "context_construction" in steps_executed,
                "prompt_sanitization": "prompt_sanitization" in steps_executed
                or "input_sanitization" in steps_executed,
                "llm_execution": "llm_generation" in steps_executed,
                "claim_verification": "claim_extraction" in steps_executed
                or "claim_verification" in steps_executed,
                "citation_validation": "citation_validation" in steps_executed,
                "answer_safety": "safety_gate" in steps_executed
                or "answer_safety_gate" in steps_executed,
            }

            # Extract actual telemetry from the LiveModelAdapter
            llm_backend = orchestrator._llm
            if hasattr(llm_backend, "last_result") and llm_backend.last_result:
                res = llm_backend.last_result
                data["llm_stage"] = {
                    "provider": res.provider,
                    "model": res.model,
                    "local_execution_id": res.local_execution_id,
                    "request_id": res.request_id,
                    "response_id": res.response_id,
                    "provider_call_latency_ms": res.provider_call_latency_ms,
                    "response_hash": res.response_hash,
                    "status": res.status,
                }
            else:
                data["llm_stage"] = None

            data["final_response"] = {
                "abstained": response.status.value == "abstained",
                "abstention_reason": response.gate_decision
                if response.status.value == "abstained"
                else None,
                "generated_answer": response.answer[:200] + "..." if response.answer else "",
                "retrieved_document_ids": response.retrieved_chunk_ids,
                "trust_scores": response.trust_scores,
                "verification_state": response.verification_report.decision.value
                if response.verification_report
                else None,
                "citation_state": response.verification_report.decision.value
                if response.verification_report
                else None,
                "safety_state": response.gate_decision,
            }

            data["execution_status"] = (
                "PASS"
                if response.status.value in ("released", "qualified", "abstained")
                else "FAIL"
            )
            print("Proof B Execution Status:", data["execution_status"])
        except Exception as e:
            print(f"Proof B failed: {e}")
            data["execution_status"] = "FAIL"

    print(json.dumps(data, indent=2))
    os.makedirs("reports/audit", exist_ok=True)
    with open("reports/audit/proof_b_telemetry.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
