"""Evidence Sources Module Init

Exposes all evidence source adapters, query router, and deduplicator.
"""

from adaptive_trust_medical_rag.evidence_sources.base_adapter import (
    AdapterExecutionMode,
    EvidenceSourceAdapter,
)
from adaptive_trust_medical_rag.evidence_sources.deduplicator import EvidenceDeduplicator
from adaptive_trust_medical_rag.evidence_sources.europepmc_adapter import EuropePMCAdapter
from adaptive_trust_medical_rag.evidence_sources.openfda_adapter import OpenFDAAdapter
from adaptive_trust_medical_rag.evidence_sources.pubmed_adapter import PubMedAdapter
from adaptive_trust_medical_rag.evidence_sources.query_router import EvidenceQueryRouter
from adaptive_trust_medical_rag.evidence_sources.rxnorm_adapter import RxNormAdapter

__all__ = [
    "AdapterExecutionMode",
    "EvidenceSourceAdapter",
    "PubMedAdapter",
    "EuropePMCAdapter",
    "RxNormAdapter",
    "OpenFDAAdapter",
    "EvidenceQueryRouter",
    "EvidenceDeduplicator",
]
