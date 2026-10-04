import sys
sys.path.insert(0, 'src')
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import BM25Retriever, Candidate
corpus = [
    Candidate(chunk_id='A', document_id='A', text='aspirin mechanism'),
    Candidate(chunk_id='B', document_id='B', text='unrelated text')
]
retriever = BM25Retriever(corpus)
scores = retriever.retrieve('aspirin mechanism')
print('Scores:')
for c, s in scores:
    print(f'{c.chunk_id}: {s}')
