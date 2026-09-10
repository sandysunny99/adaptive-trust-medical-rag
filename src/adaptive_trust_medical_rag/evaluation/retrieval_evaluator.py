import math
from dataclasses import dataclass
from typing import Any

from adaptive_trust_medical_rag.evaluation.evaluator import EvalCase
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import ScoredCandidate


@dataclass
class RetrievalMetrics:
    recall_at_1: float | None = None
    recall_at_3: float | None = None
    recall_at_5: float | None = None
    recall_at_10: float | None = None
    precision_at_5: float | None = None
    mrr: float | None = None
    ndcg_at_5: float | None = None
    # Domain metrics
    source_authority_coverage: float = 0.0

@dataclass
class CaseRetrievalRecord:
    case_id: str
    variant: str
    query_hash: str
    risk_tier: str
    claim_type: str
    retrieved_document_ids: list[str]
    retrieved_chunk_ids: list[str]
    retrieval_scores: list[float]
    source_types: list[str]
    entity_ids: list[str]
    expected_document_ids: list[str]
    relevant_retrieved_ids: list[str]
    first_relevant_rank: int | None
    metrics: RetrievalMetrics
    latency_ms: float
    channels: list[str]

def calculate_mrr(ranks: list[int]) -> float:
    if not ranks:
        return 0.0
    return 1.0 / ranks[0]

def calculate_ndcg(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    if not relevant_ids:
        return 0.0
    dcg = 0.0
    idcg = 0.0
    for i in range(min(k, len(retrieved_ids))):
        if retrieved_ids[i] in relevant_ids:
            dcg += 1.0 / math.log2(i + 2)
    for i in range(min(k, len(relevant_ids))):
        idcg += 1.0 / math.log2(i + 2)
    return dcg / idcg if idcg > 0 else 0.0

class RetrievalEvaluator:
    def __init__(self, ground_truth: dict[str, dict[str, Any]]):
        self.ground_truth = ground_truth

    def evaluate_case(
        self,
        case: EvalCase,
        variant: str,
        results: list[ScoredCandidate],
        latency_ms: float = 0.0,
        query_hash: str = ""
    ) -> CaseRetrievalRecord:
        gt = self.ground_truth.get(case.case_id, {})
        expected_docs = set(gt.get("expected_document_ids", []))
        claim_type = gt.get("claim_type", "NO_GROUND_TRUTH_EVIDENCE")

        retrieved_chunk_ids = [sc.candidate.chunk_id for sc in results]
        # Ensure we're using correct document_id
        retrieved_doc_ids = [sc.candidate.metadata.get("document_id", sc.candidate.chunk_id) for sc in results]

        relevant_retrieved = []
        ranks = []
        for i, doc_id in enumerate(retrieved_doc_ids, start=1):
            if doc_id in expected_docs:
                relevant_retrieved.append(doc_id)
                ranks.append(i)

        def calc_recall(k):
            if not expected_docs:
                return None
            hits = len(set(retrieved_doc_ids[:k]) & expected_docs)
            return hits / len(expected_docs)

        def calc_precision(k):
            if not expected_docs:
                return None
            if not retrieved_doc_ids:
                return 0.0
            k = min(k, len(retrieved_doc_ids))
            if k == 0:
                return 0.0
            hits = len(set(retrieved_doc_ids[:k]) & expected_docs)
            return hits / k

        # Calculate source authority coverage correctly
        # Count the proportion of Top 5 results that are Tier 1
        tier_1_count = 0
        k_auth = min(5, len(results))
        for sc in results[:5]:
            # According to the project, FDA Label and peer_reviewed are Tier 1
            if sc.candidate.source_authority in ["tier_1_peer_reviewed", "Tier 1", "FDA Label"]:
                tier_1_count += 1
        authority_cov = (tier_1_count / k_auth) if k_auth > 0 else 0.0

        metrics = RetrievalMetrics(
            recall_at_1=calc_recall(1),
            recall_at_3=calc_recall(3),
            recall_at_5=calc_recall(5),
            recall_at_10=calc_recall(10),
            precision_at_5=calc_precision(5),
            mrr=calculate_mrr(ranks) if expected_docs else None,
            ndcg_at_5=calculate_ndcg(retrieved_doc_ids, expected_docs, 5) if expected_docs else None,
            source_authority_coverage=authority_cov
        )

        return CaseRetrievalRecord(
            case_id=case.case_id,
            variant=variant,
            query_hash=query_hash,
            risk_tier=case.risk_tier,
            claim_type=claim_type,
            retrieved_document_ids=retrieved_doc_ids,
            retrieved_chunk_ids=retrieved_chunk_ids,
            retrieval_scores=[sc.rrf_score for sc in results],
            source_types=[sc.candidate.metadata.get("source", "unknown") for sc in results],
            entity_ids=[],
            expected_document_ids=list(expected_docs),
            relevant_retrieved_ids=relevant_retrieved,
            first_relevant_rank=ranks[0] if ranks else None,
            metrics=metrics,
            latency_ms=latency_ms,
            channels=[]
        )
