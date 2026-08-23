"""
Phase 10 — Hybrid Retrieval Engine.

Implements three retrieval channels fused via Reciprocal Rank Fusion (RRF):

  Channel 1 — BM25 lexical retrieval
    Exact entity mentions, drug names, dosages, technical terms.
    Pure-Python implementation (rank_bm25-compatible algorithm).
    No external service required.

  Channel 2 — Dense vector (cosine) retrieval
    Semantic intent matching via normalised dense embeddings.
    Interface-compatible with pgvector; unit-tested with mock embeddings.

  Channel 3 — Knowledge graph relational retrieval
    Drug-drug interaction edges, contraindication relationships,
    shared metabolic pathway (CYP3A4) traversal.
    Adjacency-list graph — drops in Neo4j adapter without API changes.

  RRF Fusion
    RRF_Score(d) = sum_c  1 / (k + rank_c(d))    k = 60 (standard)
    Top-N=50 → cross-encoder re-rank placeholder → Top-K=10 delivered
    to Adaptive Trust Engine.

All retrieval logic is pure-Python and fully unit-testable without
a live PostgreSQL / Neo4j instance.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------

#: RRF constant — standard robust value (Robertson et al., 2009)
RRF_K: int = 60
#: Number of candidates returned from RRF fusion before re-ranking
RRF_TOP_N: int = 50
#: Final number of candidates delivered to the Trust Engine
FINAL_TOP_K: int = 10


@dataclass(frozen=True)
class Candidate:
    """A single retrieved evidence chunk candidate."""

    chunk_id: str
    document_id: str
    text: str
    source_url: str = ""
    source_authority: float = 0.5
    poisoning_score: float = 0.0
    metadata: dict = field(default_factory=dict, compare=False, hash=False)


@dataclass
class ScoredCandidate:
    """Candidate annotated with retrieval scores."""

    candidate: Candidate
    bm25_rank: int | None = None  # rank in BM25 results (1-indexed); None if not retrieved
    vector_rank: int | None = None  # rank in vector results (1-indexed); None if not retrieved
    graph_rank: int | None = None  # rank in graph results (1-indexed); None if not retrieved
    rrf_score: float = 0.0
    cross_encoder_score: float | None = None
    final_rank: int | None = None

    @property
    def active_channels(self) -> int:
        """Count how many retrieval channels returned this candidate."""
        return sum(r is not None for r in (self.bm25_rank, self.vector_rank, self.graph_rank))


# ---------------------------------------------------------------------------
# BM25 Lexical Retrieval
# ---------------------------------------------------------------------------

_TOKENIZE_RE = re.compile(r"[A-Za-z0-9]+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokenizer (alphanumeric tokens only)."""
    return _TOKENIZE_RE.findall(text.lower())


class BM25Retriever:
    """
    Pure-Python BM25 retrieval (Okapi BM25).

    Tuning parameters follow the standard defaults from Robertson et al.:
      k1 = 1.5  (term frequency saturation)
      b  = 0.75 (document length normalisation)
    """

    K1: float = 1.5
    B: float = 0.75

    def __init__(self, corpus: list[Candidate]) -> None:
        self._corpus = corpus
        self._n = len(corpus)
        self._tokenized: list[list[str]] = [_tokenize(c.text) for c in corpus]
        self._doc_lengths = [len(t) for t in self._tokenized]
        self._avg_dl = sum(self._doc_lengths) / max(self._n, 1)
        self._idf: dict[str, float] = self._build_idf()
        self._tf: list[dict[str, int]] = [self._term_freq(tokens) for tokens in self._tokenized]

    def _term_freq(self, tokens: list[str]) -> dict[str, int]:
        tf: dict[str, int] = defaultdict(int)
        for token in tokens:
            tf[token] += 1
        return dict(tf)

    def _build_idf(self) -> dict[str, float]:
        df: dict[str, int] = defaultdict(int)
        for tokens in self._tokenized:
            for token in set(tokens):
                df[token] += 1
        idf: dict[str, float] = {}
        for term, freq in df.items():
            idf[term] = math.log(1 + (self._n - freq + 0.5) / (freq + 0.5))
        return idf

    def _score(self, query_tokens: list[str], doc_idx: int) -> float:
        tf = self._tf[doc_idx]
        dl = self._doc_lengths[doc_idx]
        score = 0.0
        for token in query_tokens:
            if token not in tf:
                continue
            idf = self._idf.get(token, 0.0)
            tf_val = tf[token]
            numerator = tf_val * (self.K1 + 1)
            denominator = tf_val + self.K1 * (1 - self.B + self.B * dl / self._avg_dl)
            score += idf * numerator / max(denominator, 1e-9)
        return score

    def retrieve(self, query: str, top_k: int = RRF_TOP_N) -> list[tuple[Candidate, float]]:
        """Return top_k candidates ranked by BM25 score (descending)."""
        if not self._corpus:
            return []
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []
        scores = [(self._corpus[i], self._score(query_tokens, i)) for i in range(self._n)]
        scores.sort(key=lambda x: x[1], reverse=True)
        return [(c, s) for c, s in scores[:top_k] if s > 0]


# ---------------------------------------------------------------------------
# Dense Vector (Cosine) Retrieval
# ---------------------------------------------------------------------------


@runtime_checkable
class EmbeddingModel(Protocol):
    """Protocol for pluggable embedding backends (sentence-transformers, OpenAI, etc.)."""

    def encode(self, texts: list[str]) -> list[list[float]]:
        """Return a list of dense embedding vectors for the given texts."""
        ...


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two normalised or unnormalised vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class VectorRetriever:
    """
    Dense vector retrieval using cosine similarity.

    Accepts any EmbeddingModel-compatible backend.
    In production this delegates to a pgvector ANN index.
    In unit tests a mock embedding model is injected.
    """

    def __init__(self, corpus: list[Candidate], embedding_model: EmbeddingModel) -> None:
        self._corpus = corpus
        self._model = embedding_model
        # Pre-encode corpus at construction time
        if corpus:
            self._embeddings: list[list[float]] = embedding_model.encode([c.text for c in corpus])
        else:
            self._embeddings = []

    def retrieve(self, query: str, top_k: int = RRF_TOP_N) -> list[tuple[Candidate, float]]:
        """Return top_k candidates ranked by cosine similarity (descending)."""
        if not self._corpus:
            return []
        query_emb = self._model.encode([query])[0]
        scored = [
            (self._corpus[i], _cosine_similarity(query_emb, self._embeddings[i]))
            for i in range(len(self._corpus))
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [(c, s) for c, s in scored[:top_k] if s > 0]


# ---------------------------------------------------------------------------
# Knowledge Graph Retrieval
# ---------------------------------------------------------------------------


@dataclass
class DrugRelationship:
    """A directed drug-drug edge in the knowledge graph."""

    source_drug: str  # normalised drug name / RxCUI
    target_drug: str
    relationship: str  # e.g. 'contraindication', 'interaction', 'cyp3a4_substrate'
    severity: str = "moderate"  # 'mild' | 'moderate' | 'severe' | 'contraindicated'
    chunk_id: str = ""  # evidence chunk backing this edge


class GraphRetriever:
    """
    In-memory adjacency-list knowledge graph for drug relationships.

    Designed as a drop-in interface that a Neo4j adapter can implement.
    Supports up to 2-hop traversal to surface indirect interactions.
    """

    def __init__(self, corpus: list[Candidate]) -> None:
        self._corpus = corpus
        # chunk_id -> Candidate index for fast lookup
        self._chunk_index: dict[str, int] = {c.chunk_id: i for i, c in enumerate(corpus)}
        # adjacency list: drug_name -> list[DrugRelationship]
        self._graph: dict[str, list[DrugRelationship]] = defaultdict(list)

    def add_relationship(self, rel: DrugRelationship) -> None:
        """Register a drug-drug relationship edge in the graph."""
        self._graph[rel.source_drug.lower()].append(rel)

    def retrieve(
        self,
        query_drugs: list[str],
        top_k: int = RRF_TOP_N,
        max_hops: int = 2,
    ) -> list[tuple[Candidate, float]]:
        """
        Retrieve candidates connected to any of the query drugs.

        Performs BFS up to max_hops, scoring by severity:
          contraindicated -> 1.0, severe -> 0.9, moderate -> 0.6, mild -> 0.3
        """
        if not self._corpus or not query_drugs:
            return []

        severity_score = {
            "contraindicated": 1.0,
            "severe": 0.9,
            "moderate": 0.6,
            "mild": 0.3,
        }

        visited_drugs: set[str] = set()
        frontier = [d.lower() for d in query_drugs]
        candidate_scores: dict[str, float] = {}

        for _hop in range(max_hops):
            next_frontier: list[str] = []
            for drug in frontier:
                if drug in visited_drugs:
                    continue
                visited_drugs.add(drug)
                for rel in self._graph.get(drug, []):
                    score = severity_score.get(rel.severity, 0.3)
                    if rel.chunk_id and rel.chunk_id in self._chunk_index:
                        current = candidate_scores.get(rel.chunk_id, 0.0)
                        candidate_scores[rel.chunk_id] = max(current, score)
                    next_frontier.append(rel.target_drug.lower())
            frontier = next_frontier

        results: list[tuple[Candidate, float]] = []
        for chunk_id, score in candidate_scores.items():
            idx = self._chunk_index[chunk_id]
            results.append((self._corpus[idx], score))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]


# ---------------------------------------------------------------------------
# Reciprocal Rank Fusion
# ---------------------------------------------------------------------------


def reciprocal_rank_fusion(
    ranked_lists: list[list[tuple[Candidate, float]]],
    k: int = RRF_K,
    top_n: int = RRF_TOP_N,
) -> list[ScoredCandidate]:
    """
    Fuse multiple ranked candidate lists using Reciprocal Rank Fusion.

    RRF_Score(d) = sum_{c in C}  1 / (k + rank_c(d))

    Args:
        ranked_lists: One list per retrieval channel, each containing
                      (Candidate, channel_score) tuples in rank order.
        k:            RRF smoothing constant (default 60).
        top_n:        Maximum number of fused candidates to return.

    Returns:
        ScoredCandidate list sorted by rrf_score descending.
    """
    channel_names = ["bm25", "vector", "graph"]

    # Map chunk_id -> ScoredCandidate
    scored: dict[str, ScoredCandidate] = {}

    for channel_idx, ranked in enumerate(ranked_lists):
        if channel_idx < len(channel_names):
            channel_name = channel_names[channel_idx]
        else:
            channel_name = f"ch{channel_idx}"
        for rank, (candidate, _score) in enumerate(ranked, start=1):
            cid = candidate.chunk_id
            if cid not in scored:
                scored[cid] = ScoredCandidate(candidate=candidate)
            sc = scored[cid]
            rrf_contrib = 1.0 / (k + rank)
            sc.rrf_score += rrf_contrib
            # Record per-channel rank
            if channel_name == "bm25":
                sc.bm25_rank = rank
            elif channel_name == "vector":
                sc.vector_rank = rank
            elif channel_name == "graph":
                sc.graph_rank = rank

    sorted_candidates = sorted(scored.values(), key=lambda x: x.rrf_score, reverse=True)

    # Assign final ranks
    for i, sc in enumerate(sorted_candidates[:top_n], start=1):
        sc.final_rank = i

    return sorted_candidates[:top_n]


# ---------------------------------------------------------------------------
# Hybrid Retrieval Engine (orchestrator)
# ---------------------------------------------------------------------------


class HybridRetrievalEngine:
    """
    Orchestrates BM25 + Vector + Graph retrieval channels fused via RRF.

    Usage:
        engine = HybridRetrievalEngine(corpus, embedding_model)
        engine.graph.add_relationship(DrugRelationship(...))
        results = engine.retrieve(query="warfarin drug interactions", query_drugs=["warfarin"])
    """

    def __init__(
        self,
        corpus: list[Candidate],
        embedding_model: EmbeddingModel,
        *,
        rrf_k: int = RRF_K,
        top_n: int = RRF_TOP_N,
        top_k: int = FINAL_TOP_K,
    ) -> None:
        self._rrf_k = rrf_k
        self._top_n = top_n
        self._top_k = top_k

        self.bm25 = BM25Retriever(corpus)
        self.vector = VectorRetriever(corpus, embedding_model)
        self.graph = GraphRetriever(corpus)

    def retrieve(
        self,
        query: str,
        query_drugs: list[str] | None = None,
        top_k: int | None = None,
    ) -> list[ScoredCandidate]:
        """
        Run all retrieval channels and return top_k fused candidates.

        Args:
            query:       Free-text clinical query.
            query_drugs: Optional list of normalised drug names for graph traversal.
            top_k:       Override default FINAL_TOP_K if provided.

        Returns:
            Ranked list of ScoredCandidates (final_rank 1..top_k).
            Candidates with poisoning_score > 0.4 are filtered before return.
        """
        effective_top_k = top_k if top_k is not None else self._top_k

        bm25_results = self.bm25.retrieve(query, top_k=self._top_n)
        vector_results = self.vector.retrieve(query, top_k=self._top_n)
        graph_results = self.graph.retrieve(query_drugs or [], top_k=self._top_n)

        fused = reciprocal_rank_fusion(
            [bm25_results, vector_results, graph_results],
            k=self._rrf_k,
            top_n=self._top_n,
        )

        # Evidence eligibility filter: quarantine / poisoning gate
        clean = [sc for sc in fused if sc.candidate.poisoning_score <= 0.4]

        # Re-number final ranks after filter
        for i, sc in enumerate(clean[:effective_top_k], start=1):
            sc.final_rank = i

        return clean[:effective_top_k]
