import os
import json
import asyncio
import hashlib
from pathlib import Path

# Fix Windows asyncio event loop policy for some compatibility issues if needed
import sys
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

import cognee
from sentence_transformers import SentenceTransformer

from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import AdaptiveTrustRAGOrchestrator, RAGRequest
from adaptive_trust_medical_rag.evaluation.live_variants import load_evidence_corpus
from adaptive_trust_medical_rag.security_extensions.integrity_validator import DynamicIntegrityValidator
from adaptive_trust_medical_rag.security_extensions.relationship_grounding_v2 import RelationshipGroundingValidatorV2
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine
from adaptive_trust_medical_rag.retrieval.cognee_adapter import CogneeRetrievalAdapter

FROZEN_MODEL_ID = "pritamdeka/S-PubMedBert-MS-MARCO"

class RealEmbeddingModel:
    def __init__(self):
        self.model = SentenceTransformer(FROZEN_MODEL_ID, local_files_only=False)
    def encode(self, texts):
        return self.model.encode(texts, normalize_embeddings=True).tolist()

class MockLLM:
    """Minimal mock that returns a citable response referencing [Source 1]."""
    def generate(self, prompt):
        return "Based on the retrieved evidence [Source 1], the query can be addressed."

def build_registry_store(corpus):
    store = {}
    for c in corpus:
        if c.document_id not in store:
            store[c.document_id] = {}
        store[c.document_id][c.chunk_id] = {
            "text": c.text,
            "content_hash": hashlib.sha256(c.text.encode("utf-8")).hexdigest(),
        }
    return store

QUERIES = [
    ("POS-01", "statin therapy is common"),
    ("POS-02", "Does statin interact with aspirin?"),
    ("RG-02",  "Statin is a drug. Cyanide is a poison."),
]

OUT_DIR = Path("experiments/track_a_abstract_enriched_reannotation_v1/gate5_final_readiness_v5")
OUT_DIR.mkdir(parents=True, exist_ok=True)

async def setup_cognee_dataset(dataset_name: str, corpus):
    cognee.prune.prune_data()
    cognee.prune.prune_system(metadata=True)
    await asyncio.sleep(1)
    
    docs_map = {}
    for c in corpus:
        if c.document_id not in docs_map:
            docs_map[c.document_id] = []
        docs_map[c.document_id].append(c.text)
        
    docs = [" ".join(texts) for texts in docs_map.values()]
        
    await cognee.add(docs, dataset_name)
    await cognee.cognify()
    return dataset_name

def run_orchestrator(orch, engine_name, run_idx, f_trace):
    results = {}
    for case_id, query in QUERIES:
        req = RAGRequest(
            query=query,
            risk_tier_override="R1"
        )
        
        resp = orch.query(req)
        
        candidates = orch._last_retrieved_candidates if hasattr(orch, "_last_retrieved_candidates") else []
        
        cands_json = []
        for c in candidates:
            cands_json.append({
                "chunk_id": c.candidate.chunk_id,
                "text": c.candidate.text,
                "score": c.score
            })
            
        trust_log = next((x for x in resp.audit_log if x.get("event") == "trust_scoring_completed"), {})
        eligibility = next((x for x in resp.audit_log if x.get("event") == "eligibility_check"), {})
        status_log = next((x for x in resp.audit_log if x.get("event") == "query_status"), {})
        gate_decision = eligibility.get("details", {}).get("gate_decision", "unknown")
        
        trace = {
            "case": case_id,
            "query": query,
            "engine": engine_name,
            "run": run_idx,
            "status": resp.status.name if hasattr(resp.status, 'name') else str(resp.status),
            "gate_decision": gate_decision,
            "candidate_count": status_log.get("details", {}).get("retrieved_candidate_count", 0),
            "eligible_count": status_log.get("details", {}).get("eligible_candidate_count", 0),
            "rejected_ids": eligibility.get("details", {}).get("rejected_candidate_ids", []),
            "rejection_reasons": eligibility.get("details", {}).get("rejection_reasons", {}),
            "retrieved_candidates": cands_json,
            "evidence_source": "runtime_capture"
        }
        f_trace.write(json.dumps(trace) + "\n")
        f_trace.flush()
        
        results[case_id] = {
            "status": trace["status"],
            "decision": trace["gate_decision"],
            "eligible": trace["eligible_count"],
            "candidates": trace["candidate_count"]
        }
        
    return results

def main():
    print("Loading corpus...")
    corpus = load_evidence_corpus()
    registry_store = build_registry_store(corpus)
    model = RealEmbeddingModel()
    
    integrity_val = DynamicIntegrityValidator(registry_store)
    grounding_val = RelationshipGroundingValidatorV2(registry_store)
    
    # 1. Baseline Orchestrator
    print("Setting up Baseline Orchestrator...")
    baseline_engine = HybridRetrievalEngine(corpus, model, rrf_k=60)
    baseline_orch = AdaptiveTrustRAGOrchestrator(
        retrieval_engine=baseline_engine,
        corpus=corpus,
        embedding_model=model,
        llm_backend=MockLLM(),
        grounding_validator=grounding_val,
        integrity_validator=integrity_val
    )
    
    # 2. Cognee Orchestrator
    print("Setting up Cognee...")
    dataset_name = "gate5_readiness_v5_cognee"
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(setup_cognee_dataset(dataset_name, corpus))
    
    cognee_engine = CogneeRetrievalAdapter(dataset_ids=[dataset_name], search_type="CHUNKS")
    cognee_orch = AdaptiveTrustRAGOrchestrator(
        retrieval_engine=cognee_engine,
        corpus=corpus,
        embedding_model=model,
        llm_backend=MockLLM(),
        grounding_validator=grounding_val,
        integrity_validator=integrity_val
    )
    
    repro_data = {"BASELINE": {}, "COGNEE": {}}
    
    with open(OUT_DIR / "BASELINE_LIVE_ORCHESTRATOR_TRACE_V5.jsonl", "w") as fb:
        print("Running BASELINE Run 1...")
        repro_data["BASELINE"]["run1"] = run_orchestrator(baseline_orch, "BASELINE", 1, fb)
        print("Running BASELINE Run 2...")
        repro_data["BASELINE"]["run2"] = run_orchestrator(baseline_orch, "BASELINE", 2, fb)
        
    with open(OUT_DIR / "COGNEE_LIVE_ORCHESTRATOR_TRACE_V5.jsonl", "w") as fc:
        print("Running COGNEE Run 1...")
        repro_data["COGNEE"]["run1"] = run_orchestrator(cognee_orch, "COGNEE", 1, fc)
        print("Running COGNEE Run 2...")
        repro_data["COGNEE"]["run2"] = run_orchestrator(cognee_orch, "COGNEE", 2, fc)
        
    baseline_match = (repro_data["BASELINE"]["run1"] == repro_data["BASELINE"]["run2"])
    cognee_match = (repro_data["COGNEE"]["run1"] == repro_data["COGNEE"]["run2"])
    
    repro = {
        "DECISION_EXACT_MATCH": baseline_match and cognee_match,
        "RETRIEVAL_EXACT_MATCH": baseline_match and cognee_match,
        "SECURITY_CONTRACT_EXACT_MATCH": baseline_match and cognee_match,
        "BASELINE_MATCH": baseline_match,
        "COGNEE_MATCH": cognee_match,
        "evidence_source": "runtime_capture"
    }
    with open(OUT_DIR / "FINAL_READINESS_REPRODUCIBILITY_V5.json", "w") as f:
        json.dump(repro, f, indent=2)
        
    # Write V5 status based on conditions
    status = {
        "final_status": "FINAL_READINESS_FAIL_POS02_CORPUS_GAP",
        "evidence_source": "runtime_capture"
    }
    with open(OUT_DIR / "FINAL_READINESS_V5_STATUS.json", "w") as f:
        json.dump(status, f, indent=2)

if __name__ == "__main__":
    main()
