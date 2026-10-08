import json
import os
import time
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass

from adaptive_trust_medical_rag.llm_backend.groq_backend import GroqBackend
from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import build_grounded_prompt
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, ScoredCandidate
from adaptive_trust_medical_rag.trust_scoring.trust_scorer import AdaptiveTrustScorer, TrustFactorScores
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2, EvidenceChunk
@dataclass
class EvaluationResult:
    claim_support_rate: float
    citation_validation_rate: float
    unsupported_answer_rate: float
    abstention_rate: float
    provider_failure_rate: float


# Ensure execution is authorized
if os.environ.get("RESEARCH_EVAL_AUTHORIZED") != "1":
    print("Execution rejected: RESEARCH_EVAL_AUTHORIZED environment variable not set to 1.")
    exit(1)

def main():
    print("Starting V1.2 160-Request Evaluation")
    
    # Paths
    run_dir = Path("experiments/runs/real-llm-v1_2/REAL_LLM_V1_2_RUN_001")
    run_dir.mkdir(parents=True, exist_ok=True)
    results_path = run_dir / "results.jsonl"
    metrics_path = run_dir / "metrics.json"
    
    # Load cases
    with open("experiments/manifests/v3_1_human_cases.json", "r") as f:
        cases = json.load(f)
        
    # Load retrieval mapping (FROZEN_HISTORICAL_OUTPUT)
    with open("experiments/runs/retrieval-diagnostic-phase2f5-simulated/f3_results.jsonl", "r") as f:
        f3_lines = [json.loads(line) for line in f]
    retrieval_map = {line["query_id"]: line["top_5"] for line in f3_lines}
    
    # Load documents
    with open("experiments/evidence_snapshots/retrieval-v3-real/documents.json", "r") as f:
        docs = json.load(f)
    doc_map = {d["document_id"]: d for d in docs}
    
    # Load Prompt
    with open("experiments/prompts/REAL_LLM_EVALUATION_PROMPT_V1_2.txt", "r") as f:
        prompt_template = f.read()
    prompt_hash = hashlib.sha256(prompt_template.encode('utf-8')).hexdigest()
    
    # Initialize components
    backend = GroqBackend(
        api_key=os.environ.get("GROQ_API_KEY", ""),
        model_name="openai/gpt-oss-120b",
        temperature=0.0
    )
    
    verifier = ClaimVerifierV2()
    trust_scorer = AdaptiveTrustScorer()
    
    metrics_log = {
        "arm_a": {"total": 0, "claim_support": 0, "citation_val": 0, "unsupported": 0, "abstention": 0, "provider_failures": 0},
        "arm_b": {"total": 0, "claim_support": 0, "citation_val": 0, "unsupported": 0, "abstention": 0, "provider_failures": 0}
    }
    
    def log_result(arm, case_id, request_id, status, metrics, result_dict):
        metrics_log[arm]["total"] += 1
        if status == "provider_failure":
            metrics_log[arm]["provider_failures"] += 1
        elif status == "abstained":
            metrics_log[arm]["abstention"] += 1
        elif status == "SUCCESS":
            metrics_log[arm]["claim_support"] += metrics.claim_support_rate
            metrics_log[arm]["citation_val"] += metrics.citation_validation_rate
            metrics_log[arm]["unsupported"] += metrics.unsupported_answer_rate
            
        with open(results_path, "a") as out_f:
            out_f.write(json.dumps(result_dict) + "\n")
            
    # Execute exactly 80 cases * 2 arms = 160 requests
    # Order: case 1 Arm A, case 1 Arm B, case 2 Arm A, case 2 Arm B...
    for case in cases:
        case_id = case["case_id"]
        query = case["query"]
        risk_tier = case["risk_tier"]
        
        # Get frozen evidence
        top_ids = retrieval_map.get(case_id, [])
        scored_candidates = []
        for i, doc_id in enumerate(top_ids):
            doc = doc_map.get(doc_id)
            if doc:
                candidate = Candidate(
                    chunk_id=doc["chunk_id"],
                    text=doc["text"],
                    document_id=doc_id,
                    metadata=doc,
                    source_authority=1.0 if doc.get("authority_tier") == "PubMed_Central" else 0.8
                )
                scored_candidates.append(ScoredCandidate(candidate=candidate, rrf_score=1.0 - (i*0.1)))
                
        evidence_chunks = [
            EvidenceChunk(
                chunk_id=sc.candidate.chunk_id,
                text=sc.candidate.text,
                source_authority=sc.candidate.source_authority,
                citation_index=i+1,
                trust_score=1.0
            ) for i, sc in enumerate(scored_candidates)
        ]
        
        for arm in ["arm_a", "arm_b"]:
            import uuid
            request_id = f"req_{uuid.uuid4().hex[:8]}"
            t0 = time.time()
            
            # Form evidence and prompt
            arm_candidates = scored_candidates
            abstain_reason = None
            status = "SUCCESS"
            response_text = ""
            error_status = None
            
            if arm == "arm_b":
                # Apply Evidence Eligibility Gate
                eligible = []
                for sc in scored_candidates:
                    score = trust_scorer.score(
                        chunk_id=sc.candidate.chunk_id,
                        risk_class=risk_tier,
                        factors=TrustFactorScores(
                            source_authority=sc.candidate.source_authority,
                            query_relevance=0.8,
                            evidence_quality=0.8,
                            freshness=1.0,
                            entity_match=1.0,
                            anti_poisoning=1.0,
                            anti_injection=1.0
                        )
                    )
                    if score.is_eligible:
                        eligible.append(sc)
                
                arm_candidates = eligible
                if not eligible:
                    status = "abstained"
                    abstain_reason = "No eligible evidence survived trust scoring"
            
            if status != "abstained":
                # Prompt Instantiation (we use prompt_instantiator but for simplicity just exact replace)
                from experiments.real_llm_evaluation.prompt_instantiator import instantiate_prompt
                
                evidence_lines = []
                for i, sc in enumerate(arm_candidates, start=1):
                    evidence_lines.append(f"[Source {i}] (chunk={sc.candidate.chunk_id})\n{sc.candidate.text}")
                evidence_block = "\n\n".join(evidence_lines) if evidence_lines else "(No evidence retrieved)"
                
                try:
                    final_prompt = instantiate_prompt(
                        prompt_template,
                        query=query,
                        patient_context=case.get("patient_context", "None"),
                        risk_tier=risk_tier,
                        evidence_block=evidence_block
                    )
                    
                    import asyncio
                    # Groq Backend
                    gen_res = asyncio.run(backend.generate(prompt=final_prompt, response_format={"type": "json_object"}))
                    response_text = gen_res.response_text
                except Exception as e:
                    status = "provider_failure"
                    error_status = str(e)
            
            # Safety Gate / Verification
            eval_metrics = None
            safety_status = "UNKNOWN"
            if status == "SUCCESS":
                report = verifier.verify(response_text, evidence_chunks)
                
                # Compute V1.2 metrics
                total_claims = len(report.judgments)
                supported = sum(1 for j in report.judgments if j.support_state == "SUPPORTED")
                unsupported = sum(1 for j in report.judgments if j.support_state == "UNSUPPORTED")
                total_citations = sum(1 for j in report.judgments if j.citation_validation.citation_present)
                valid_citations = sum(1 for j in report.judgments if j.citation_validation.citation_supports_claim)
                
                eval_metrics = EvaluationResult(
                    claim_support_rate=(supported / total_claims) if total_claims > 0 else 0.0,
                    citation_validation_rate=(valid_citations / total_citations) if total_citations > 0 else 0.0,
                    unsupported_answer_rate=1.0 if unsupported > 0 else 0.0,
                    abstention_rate=0.0,
                    provider_failure_rate=0.0
                )
                
                if arm == "arm_b":
                    # Answer Safety Gate logic - if unsupported claims, arm_b abstains post-generation
                    if eval_metrics.unsupported_answer_rate > 0:
                        status = "abstained"
                        abstain_reason = "Answer contained unsupported claims (Answer Safety Gate)"
            
            if status == "abstained" and not eval_metrics:
                eval_metrics = EvaluationResult(0.0, 0.0, 0.0, 1.0, 0.0)
            
            # Record Result
            result_record = {
                "run_id": "REAL_LLM_V1_2_RUN_001",
                "request_id": request_id,
                "case_id": case_id,
                "arm": arm,
                "provider": "Groq",
                "model": "openai/gpt-oss-120b",
                "prompt_version": "V1.2",
                "prompt_hash": prompt_hash,
                "retrieval_identity": "FROZEN_HISTORICAL_OUTPUT",
                "timestamp_start": datetime.fromtimestamp(t0, timezone.utc).isoformat(),
                "timestamp_end": datetime.now(timezone.utc).isoformat(),
                "status": status,
                "structured_answer": response_text if status == "SUCCESS" else None,
                "abstention": abstain_reason,
                "safety_status": safety_status,
                "provider_status": "SUCCESS" if status != "provider_failure" else "FAILURE",
                "error_status": error_status,
                "metrics": eval_metrics.__dict__ if eval_metrics else None
            }
            log_result(arm, case_id, request_id, status, eval_metrics, result_record)

    # Save metrics
    total = sum(metrics_log[a]["total"] for a in ["arm_a", "arm_b"])
    final_metrics = {
        "protocol_version": "1.2",
        "run_id": "REAL_LLM_V1_2_RUN_001",
        "n_cases": len(cases),
        "n_arm_a": metrics_log["arm_a"]["total"],
        "n_arm_b": metrics_log["arm_b"]["total"],
        "n_total": total,
        "medical_ground_truth_available": False,
        "arm_a_metrics": {k: v / (metrics_log["arm_a"]["total"] or 1) for k, v in metrics_log["arm_a"].items() if k != "total"},
        "arm_b_metrics": {k: v / (metrics_log["arm_b"]["total"] or 1) for k, v in metrics_log["arm_b"].items() if k != "total"}
    }
    with open(metrics_path, "w") as f:
        json.dump(final_metrics, f, indent=2)
        
    print("Execution complete.")

if __name__ == "__main__":
    main()
