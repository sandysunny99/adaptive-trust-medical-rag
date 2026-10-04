import json
import time
from pathlib import Path

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import BM25Retriever, Candidate, HybridRetrievalEngine
from adaptive_trust_medical_rag.evaluation.live_variants import load_evidence_corpus, SimpleEmbeddingModel
from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import AdaptiveTrustRAGOrchestrator, RAGRequest

class MockLLM:
    def __init__(self):
        self.provider = "mock"
        self.model_name = "mock"
    def generate_with_metadata(self, prompt: str):
        class Res:
            response_text = "MOCK_RESPONSE"
        return Res()
    def generate(self, prompt: str):
        return "MOCK_RESPONSE"
    async def agenerate(self, prompt: str):
        return "MOCK_RESPONSE"

class MockTrustScorer:
    def score(self, candidate_id: str, risk_class: str, factors: any):
        class TSRes:
            trust_score = 0.99
            is_eligible = True
            factors = {"authority": 0.95}
            threshold_applied = 0.45
            risk_class = risk_class
        return TSRes()

def main():
    out_dir = Path("experiments/track_a_abstract_enriched_reannotation_v1/retrieval_primitive_repair_v1")
    corpus = load_evidence_corpus()
    hybrid = HybridRetrievalEngine(corpus, SimpleEmbeddingModel())
    
    orch = AdaptiveTrustRAGOrchestrator(
        corpus=corpus,
        embedding_model=SimpleEmbeddingModel(),
        llm_backend=MockLLM(),
        trust_scorer=MockTrustScorer()
    )
    orch._retrieval = hybrid
    
    req = RAGRequest(query="Does statin interact with aspirin?", risk_tier_override="R1")
    trace_res = orch.query(req)
    
    with open(out_dir / "RETRIEVAL_TO_SECURITY_TRACE.jsonl", "w", encoding="utf-8") as f:
        f.write(json.dumps({
            "case": "POS-02",
            "query": req.query,
            "candidates_evaluated": len(trace_res.retrieved_chunk_ids),
            "orch_status": trace_res.status.value if hasattr(trace_res.status, "value") else str(trace_res.status),
            "evidence_source": "runtime_capture"
        }) + "\n")

if __name__ == '__main__':
    main()
