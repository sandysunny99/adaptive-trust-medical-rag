import asyncio
import os
import json
import time
from dotenv import load_dotenv
load_dotenv(".env.local")

# Ensure key is set in python context
# Load from environment variables which are now populated
# os.environ["GROQ_API_KEY"] = "..." (Removed to prevent leak)

import logging
logging.basicConfig(level=logging.INFO)

from adaptive_trust_medical_rag.services.live_application import LiveMedicalRAGService
from adaptive_trust_medical_rag.normalization.drug_normalizer import DrugNormalizer
from adaptive_trust_medical_rag.llm_backend.groq_backend import GroqBackend
from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2
from adaptive_trust_medical_rag.trust_scoring.trust_scorer import AdaptiveTrustScorer
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine, Candidate, ScoredCandidate

class MockState:
    pass

state = MockState()
state.drug_normalizer = DrugNormalizer(use_api=True)
state.llm_backend = GroqBackend(api_key=os.environ["GROQ_API_KEY"], temperature=0.0)
state.claim_verifier = ClaimVerifierV2()
state.trust_scorer = AdaptiveTrustScorer()

class MockVectorIndex:
    def __init__(self, chunks):
        self.chunks = chunks
    def search(self, query, top_k):
        return []

class MockBM25Index:
    def __init__(self, chunks):
        self.chunks = chunks
    def search(self, query, top_k):
        return []

class MockDB:
    def get_document_by_id(self, doc_id):
        return {}

class MockRetrievalEngine(HybridRetrievalEngine):
    def retrieve(self, query, query_drugs, top_k, risk_tier=None):
        print("MOCK RETRIEVE CALLED!")
        results = []
        for c in self._chunks:
            cand = Candidate(
                chunk_id=c["chunk_id"],
                document_id=c["document_id"],
                text=c["text"],
                source_authority=c["authority"]
            )
            cand.metadata["source_type"] = c["source_type"]
            cand.metadata["freshness"] = c["freshness"]
            cand.metadata["freshness_score"] = c["freshness"]
            cand.metadata["provenance"] = c.get("provenance", {})
            sc = ScoredCandidate(candidate=cand, rrf_score=1.0)
            results.append(sc)
        print("MOCK RETRIEVE RETURNED:", len(results), "RESULTS")
        return results

def load_live_corpus():
    with open("data/live_medical/LIVE_MEDICAL_CORPUS_V1.json", "r", encoding="utf-8") as f:
        chunks = json.load(f)
    
    candidates = []
    for c in chunks:
        cand = Candidate(
            chunk_id=c["chunk_id"],
            document_id=c["document_id"],
            text=c["text"],
            source_authority=c["authority"]
        )
        cand.metadata["source_type"] = c["source_type"]
        cand.metadata["freshness"] = c["freshness"]
        cand.metadata["provenance"] = c.get("provenance", {})
        candidates.append(cand)
        
    class MockEmbeddingModel:
        def encode(self, texts):
            return [[0.0] * 768 for _ in texts]
            
    engine = MockRetrievalEngine(candidates, MockEmbeddingModel())
    engine._chunks = chunks
    return engine

state.retrieval_engine = load_live_corpus()

async def run_test():
    service = LiveMedicalRAGService(state)
    request_id = "test-v5-run"
    drug_names = ["warfarin overdose"]
    start_time = time.time()
    
    print("--- STARTING LIVE RAG SERVICE ---")
    events = []
    
    async for event in service.execute(request_id, drug_names, None, start_time):
        print(f"EVENT: {event['event']}")
        if event["event"] == "trust":
             print("TRUST EVALUATION PAYLOAD:", json.dumps(event["data"], indent=2))
        elif event["event"] == "result":
            print("FINAL DECISION:", event["data"].get("gate_decision"))
            print("CLAIMS:")
            for c in event["data"].get("claims", []):
                print(f"  - {c['support_state']}: {c['text']}")
        elif event["event"] == "error" or event["event"] == "abstention":
            print("TERMINAL EVENT PAYLOAD:", json.dumps(event["data"], indent=2))
        events.append(event)
        
    print("--- COMPLETED ---")
    
    with open("v5_events.json", "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, default=str)

if __name__ == "__main__":
    asyncio.run(run_test())
