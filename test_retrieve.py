from adaptive_trust_medical_rag.evaluation.live_variants import _make_default_corpus
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import BM25Retriever, _tokenize

corpus = _make_default_corpus()
b = BM25Retriever(corpus)
q = "Is aspirin contraindicated with warfarin?"
qt = _tokenize(q)
print("Q tokens:", qt)
for i, c in enumerate(corpus):
    score = b._score(qt, i)
    print(i, score)
    print(c.text)