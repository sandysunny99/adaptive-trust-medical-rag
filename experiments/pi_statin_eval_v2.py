import json
import asyncio
import os
import sys

sys.path.insert(0, os.path.abspath('src'))
os.environ['HF_HOME'] = os.path.abspath('cognee_service/model_cache/huggingface')

from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import AdaptiveTrustRAGOrchestrator, RAGRequest
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import HybridRetrievalEngine
from adaptive_trust_medical_rag.retrieval.cognee_adapter import CogneeRetrievalAdapter
from adaptive_trust_medical_rag.evaluation.live_variants import load_evidence_corpus
from adaptive_trust_medical_rag.security_extensions.relationship_grounding_v2 import RelationshipGroundingValidatorV2
from adaptive_trust_medical_rag.trust_scoring.trust_scorer import AdaptiveTrustScorer

# Check if real LLM is available
api_key = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY')
if not api_key:
    print("BLOCKED_REAL_LLM")
    sys.exit(0)

# If it had an API key, we would proceed with loading real model...
