content = '''# CI Healthcheck Dependency Audit

| Dependency | Loaded by | Required for API health? | Heavy? | External network? |
|---|---|---|---|---|
| pritamdeka/PubMedBERT-MNLI-MedNLI (NLI Model) | ClaimVerifierV2.__init__ in create_app() | No | Yes (250MB+) | Yes (HF Hub) |
| sentence-transformers/all-MiniLM-L6-v2 (Embeddings) | LiveEmbeddingModel.__init__ in create_app() | No | Yes (90MB+) | Yes (HF Hub) |

## Analysis
The create_app() function synchronously initializes these deep learning models when the module is imported or instantiated. Because check_api_health.py runs rom adaptive_trust_medical_rag.api.app import create_app; app = create_app(), it forces the download and loading of all Hugging Face model weights simply to query the /health endpoint. This conflates LIVENESS with READINESS.
'''
open('CI_HEALTHCHECK_DEPENDENCY_AUDIT.md', 'w').write(content)
