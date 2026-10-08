content = open('src/adaptive_trust_medical_rag/services/live_application.py').read()
content = content.replace('live_corpus.append(Candidate(', 'from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate\n                    live_corpus.append(Candidate(')
open('src/adaptive_trust_medical_rag/services/live_application.py', 'w').write(content)
