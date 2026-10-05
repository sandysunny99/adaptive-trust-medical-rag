import asyncio
import time
from dataclasses import dataclass
from typing import Any

import cognee

from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import Candidate, ScoredCandidate


@dataclass
class CogneeOutput:
    query: str
    search_type: str
    dataset_id: str
    result_data: Any
    latency: float

class EvidenceMapper:
    """Maps raw Cognee output shapes into the rigorous EvidenceCandidate (Candidate) contract."""

    @staticmethod
    def map_chunks(output: CogneeOutput) -> list[Candidate]:
        candidates = []
        if not isinstance(output.result_data, list):
            return candidates

        for item in output.result_data:
            # Deterministic identity mapping
            raw_doc_name = item.get('document_name', '')
            doc_id = raw_doc_name.replace('.txt', '') if raw_doc_name else item.get('document_id')
            chunk_idx = item.get('chunk_index', 0)
            chunk_id = f"chunk_{chunk_idx}"

            score = item.get('score')
            rank = item.get('rank')
            source_authority = item.get('source_authority', 0.5)

            status = "FULL" if (chunk_id and doc_id) else "PROVENANCE_MISSING"
            provenance_dict = {
                "source": item.get("source", "pubmed"),
                "document_id": str(doc_id),
                "chunk_id": chunk_id,
                "status": status,
                "cognee_internal_id": str(item.get('id', ''))
            } if status == "FULL" else {}

            c = Candidate(
                chunk_id=chunk_id,
                document_id=str(doc_id) if doc_id else "unknown",
                text=item.get('text', ''),
                source_authority=source_authority,
                poisoning_score=0.0,
                metadata={
                    "score": score if score is not None else "NOT_AVAILABLE",
                    "rank": rank if rank is not None else "NOT_AVAILABLE",
                    "document_name": raw_doc_name,
                    "search_type": output.search_type,
                    "provenance_status": status,
                    "provenance": provenance_dict
                }
            )
            candidates.append(c)
        return candidates

    @staticmethod
    def map_hybrid_completion(output: CogneeOutput) -> list[Candidate]:
        if not isinstance(output.result_data, str):
            return []
        return [Candidate(
            chunk_id=f"hybrid_compound_{output.dataset_id}",
            document_id=f"hybrid_compound_{output.dataset_id}",
            text=output.result_data,
            source_authority=0.5,
            poisoning_score=0.0,
            metadata={
                "search_type": output.search_type,
                "is_compound": True,
                "score": "NOT_AVAILABLE",
                "rank": "NOT_AVAILABLE",
                "provenance_status": "PROVENANCE_PARTIAL",
                "provenance": {
                    "source": "cognee_hybrid",
                    "status": "PROVENANCE_PARTIAL"
                }
            }
        )]

    @classmethod
    def map(cls, output: CogneeOutput) -> list[Candidate]:
        if output.search_type == "CHUNKS":
            return cls.map_chunks(output)
        elif output.search_type == "HYBRID_COMPLETION":
            return cls.map_hybrid_completion(output)
        else:
            return []

class CogneeRetrievalAdapter:
    """Canonical adapter that integrates Adaptive Trust RAG Orchestrator with the real Cognee engine."""
    def __init__(self, dataset_ids: list[str] = None, search_type: str = "CHUNKS"):
        self.dataset_ids = dataset_ids
        self.search_type = search_type

    def retrieve(self, query: str, query_drugs: list[str] = None, top_k: int = 5) -> list[ScoredCandidate]:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.retrieve_async(query, top_k))

    async def retrieve_async(self, query: str, top_k: int = 5) -> list[ScoredCandidate]:
        start_time = time.time()
        search_enum = getattr(cognee.SearchType, self.search_type)

        if self.dataset_ids:
            results = await cognee.search(query, search_enum, datasets=self.dataset_ids)
        else:
            results = await cognee.search(query, search_enum)

        flat_results = []
        for d in results:
            if isinstance(d, dict) and 'search_result' in d:
                flat_results.extend(d['search_result'])
            else:
                flat_results.append(d)

        latency = time.time() - start_time

        output = CogneeOutput(
            query=query,
            search_type=self.search_type,
            dataset_id=self.dataset_ids[0] if self.dataset_ids else "unknown",
            result_data=flat_results,
            latency=latency
        )

        candidates = EvidenceMapper.map(output)

        scored_candidates = []
        for cand in candidates[:top_k]:
            score = cand.metadata.get("score", 1.0)
            if score == "NOT_AVAILABLE": score = 1.0
            scored_candidates.append(ScoredCandidate(candidate=cand, rrf_score=float(score)))

        return scored_candidates
