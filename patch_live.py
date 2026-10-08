import os

file_path = 'src/adaptive_trust_medical_rag/services/live_application.py'
content = open(file_path).read()

lazy_load_code = '''
def _lazy_init_models(app_state):
    import os
    import logging
    log = logging.getLogger(__name__)
    
    if getattr(app_state, "claim_verifier", None) is None:
        from adaptive_trust_medical_rag.verification.claim_verifier_v2 import ClaimVerifierV2
        log.info("Lazy loading ClaimVerifierV2 (heavy model download)")
        app_state.claim_verifier = ClaimVerifierV2()
        
    if getattr(app_state, "retrieval_engine", None) is None:
        try:
            import json
            from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import (
                Candidate,
                HybridRetrievalEngine,
            )
            corpus_path = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "live_medical", "LIVE_MEDICAL_CORPUS_V2.json")
            live_corpus = []
            if os.path.exists(corpus_path):
                with open(corpus_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for item in data:
                    live_corpus.append(Candidate(
                        chunk_id=item["chunk_id"],
                        document_id=item["document_id"],
                        text=item["text"],
                        source_url=item.get("document_url", ""),
                        source_authority=item.get("authority", 0.5),
                        metadata={
                            "provenance": item.get("provenance", {}),
                            "freshness_score": item.get("freshness", 0.8),
                            "source_type": item.get("source_type")
                        }
                    ))
                class LiveEmbeddingModel:
                    def __init__(self, data_items):
                        self.text_to_emb = {i["text"]: i["embedding"] for i in data_items if "embedding" in i}
                        from sentence_transformers import SentenceTransformer
                        self.model = SentenceTransformer("all-MiniLM-L6-v2")

                    def encode(self, texts):
                        results = []
                        texts_to_compute = []
                        indices_to_compute = []
                        for i, t in enumerate(texts):
                            if t in self.text_to_emb:
                                results.append(self.text_to_emb[t])
                            else:
                                results.append(None)
                                texts_to_compute.append(t)
                                indices_to_compute.append(i)
                        if texts_to_compute:
                            computed = self.model.encode(texts_to_compute).tolist()
                            for i, idx in enumerate(indices_to_compute):
                                results[idx] = computed[i]
                        return results
                
                log.info("Lazy loading HybridRetrievalEngine (heavy model download)")
                app_state.retrieval_engine = HybridRetrievalEngine(live_corpus, LiveEmbeddingModel(data))
            else:
                app_state.retrieval_engine = HybridRetrievalEngine([], None)
        except Exception as e:
            log.warning("Could not lazy init retrieval engine: %s", e)
            app_state.retrieval_engine = None

'''

content = content + "\n\n" + lazy_load_code
content = content.replace('self.llm = getattr(self.app_state, "llm_backend", None)', '_lazy_init_models(self.app_state)\n        self.llm = getattr(self.app_state, "llm_backend", None)')

open(file_path, 'w').write(content)
