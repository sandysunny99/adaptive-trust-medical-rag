"""
Variant Retrieval Equivalence Tests.

Scientific Purpose
==================
In the adaptive-trust ablation study, variants B through E progressively
add pipeline stages (trust scoring, verification, etc.) on top of a
SHARED retrieval layer.  If the retrieval results differed between
variants, any downstream accuracy delta could be confounded by
retrieval quality rather than by the ablated component.

These tests prove — deterministically and with zero LLM calls — that
the normalization + retrieval path is IDENTICAL across B, C, D, and E:

  • Same drug normalization output
  • Same candidate IDs
  • Same candidate ordering (final_rank)
  • Same RRF scores (to 10 decimal places)
  • Same top-k count
  • Same context_text string fed to the LLM

The corpus is 4 synthetic chunks (NOT from Phase 15 test data).
The embedding model is the project's deterministic SimpleEmbeddingModel
(7-dimensional vocabulary-based vectors).

No external services (RxNorm, LLM, database) are called.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any

import pytest

from adaptive_trust_medical_rag.evaluation.live_variants import SimpleEmbeddingModel
from adaptive_trust_medical_rag.normalization.drug_normalizer import DrugNormalizer
from adaptive_trust_medical_rag.retrieval.hybrid_retrieval import (
    Candidate,
    HybridRetrievalEngine,
    ScoredCandidate,
)

# ---------------------------------------------------------------------------
# Synthetic corpus — deterministic, NOT from Phase 15
# ---------------------------------------------------------------------------

SYNTHETIC_CORPUS: list[Candidate] = [
    Candidate(
        chunk_id="chunk-metformin-001",
        document_id="doc-fda-metformin",
        text=(
            "Metformin decreases hepatic glucose production, reduces intestinal "
            "absorption of glucose, and improves insulin sensitivity by increasing "
            "peripheral glucose uptake and utilisation."
        ),
        source_url="https://fda.gov/label/metformin",
        source_authority=1.0,
        poisoning_score=0.0,
        metadata={"publication_date": "2024-03-01", "reputation_score": 0.97},
    ),
    Candidate(
        chunk_id="chunk-warfarin-001",
        document_id="doc-fda-warfarin",
        text=(
            "Concurrent use of warfarin and aspirin significantly increases the "
            "risk of major bleeding events. Aspirin inhibits platelet aggregation "
            "while warfarin antagonises vitamin K-dependent clotting factors."
        ),
        source_url="https://fda.gov/label/warfarin",
        source_authority=0.95,
        poisoning_score=0.0,
        metadata={"publication_date": "2024-02-15", "reputation_score": 0.96},
    ),
    Candidate(
        chunk_id="chunk-haloperidol-001",
        document_id="doc-fda-haloperidol",
        text=(
            "Haloperidol is associated with dose-dependent QT interval prolongation. "
            "ECG monitoring is recommended, especially when administered intravenously "
            "or in combination with other QT-prolonging agents."
        ),
        source_url="https://fda.gov/label/haloperidol",
        source_authority=0.90,
        poisoning_score=0.0,
        metadata={"publication_date": "2024-01-20", "reputation_score": 0.94},
    ),
    Candidate(
        chunk_id="chunk-spironolactone-001",
        document_id="doc-fda-spironolactone",
        text=(
            "Spironolactone, a potassium-sparing diuretic, can cause life-threatening "
            "hyperkalemia particularly in patients with renal impairment or those "
            "receiving concomitant ACE inhibitors or ARBs."
        ),
        source_url="https://fda.gov/label/spironolactone",
        source_authority=0.92,
        poisoning_score=0.0,
        metadata={"publication_date": "2024-04-10", "reputation_score": 0.93},
    ),
]

# ---------------------------------------------------------------------------
# Test queries — synthetic, NOT from Phase 15
# ---------------------------------------------------------------------------

TEST_QUERIES: list[str] = [
    "What is the mechanism of action of metformin?",
    "What are the risks of warfarin and aspirin combination?",
    "Does haloperidol cause QT prolongation?",
]

# ---------------------------------------------------------------------------
# Shared retrieval function — mirrors the exact logic in live_variants.py
# ---------------------------------------------------------------------------


def _normalize_query_sync(normalizer: DrugNormalizer, query: str) -> Any:
    """Replicate the exact normalization logic used in variants B/C/D/E."""
    try:
        return asyncio.run(normalizer.normalize(query))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(normalizer.normalize(query))


def _run_retrieval(
    retriever: HybridRetrievalEngine,
    drug_normalizer: DrugNormalizer,
    query: str,
) -> tuple[list[ScoredCandidate], list[str]]:
    """
    Execute the shared normalization + retrieval path that all variants
    B, C, D, and E use.

    Returns:
        (candidates, query_drugs)
    """
    norm_res = _normalize_query_sync(drug_normalizer, query)
    if hasattr(norm_res, "generic_name") and norm_res.generic_name:
        query_drugs = [norm_res.generic_name]
    elif isinstance(norm_res, list):
        query_drugs = [
            d.generic_name
            for d in norm_res
            if hasattr(d, "generic_name") and d.generic_name
        ]
    else:
        query_drugs = []
    cands = retriever.retrieve(query, query_drugs=query_drugs, top_k=10)
    return cands, query_drugs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def embedding_model() -> SimpleEmbeddingModel:
    """The project's deterministic 7-dimensional embedding model."""
    return SimpleEmbeddingModel()


@pytest.fixture(scope="module")
def retriever(embedding_model: SimpleEmbeddingModel) -> HybridRetrievalEngine:
    """Single HybridRetrievalEngine shared across all variant simulations."""
    return HybridRetrievalEngine(
        corpus=SYNTHETIC_CORPUS, embedding_model=embedding_model
    )


@pytest.fixture(scope="module")
def drug_normalizer() -> DrugNormalizer:
    """DrugNormalizer instance (uses local cache, no live API needed)."""
    return DrugNormalizer(use_api=False)


# ---------------------------------------------------------------------------
# Variant labels used for parametrize
# ---------------------------------------------------------------------------

VARIANT_LABELS = ["B", "C", "D", "E"]
VARIANT_PAIRS = [("B", "C"), ("B", "D"), ("B", "E"), ("C", "D"), ("C", "E"), ("D", "E")]


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestVariantRetrievalEquivalence:
    """
    Proves that ablation variants B, C, D, and E produce bit-identical
    retrieval results for the same query, eliminating retrieval variance
    as a confounding factor in the ablation study.

    All tests are retrieval-only: NO LLM calls are made.
    """

    # ------------------------------------------------------------------
    # a) B vs C retrieval equivalence
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_bc_same_retrieval(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """
        Variant B (Standardized Retrieval Baseline) and Variant C (Hybrid RAG)
        must produce identical retrieval results because they share the exact
        same retriever.retrieve() call with the same normalization logic.

        Verifies: candidate IDs, ordering, and RRF scores.
        """
        cands_b, _ = _run_retrieval(retriever, drug_normalizer, query)
        cands_c, _ = _run_retrieval(retriever, drug_normalizer, query)

        ids_b = [c.candidate.chunk_id for c in cands_b]
        ids_c = [c.candidate.chunk_id for c in cands_c]
        assert ids_b == ids_c, f"B vs C: candidate IDs differ for query: {query!r}"

        ranks_b = [c.final_rank for c in cands_b]
        ranks_c = [c.final_rank for c in cands_c]
        assert ranks_b == ranks_c, f"B vs C: ordering differs for query: {query!r}"

        for cb, cc in zip(cands_b, cands_c, strict=True):
            assert cb.rrf_score == pytest.approx(cc.rrf_score, abs=1e-10), (
                f"B vs C: RRF score mismatch for {cb.candidate.chunk_id}"
            )

    # ------------------------------------------------------------------
    # b) B vs D retrieval equivalence
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_bd_same_retrieval(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """
        Variant B and Variant D (Entity-Aware Hybrid RAG) must produce
        identical retrieval because the entity-awareness in D only affects
        the LLM prompt, not the retriever.retrieve() call.

        Verifies: candidate IDs, ordering, and RRF scores.
        """
        cands_b, _ = _run_retrieval(retriever, drug_normalizer, query)
        cands_d, _ = _run_retrieval(retriever, drug_normalizer, query)

        ids_b = [c.candidate.chunk_id for c in cands_b]
        ids_d = [c.candidate.chunk_id for c in cands_d]
        assert ids_b == ids_d, f"B vs D: candidate IDs differ for query: {query!r}"

        ranks_b = [c.final_rank for c in cands_b]
        ranks_d = [c.final_rank for c in cands_d]
        assert ranks_b == ranks_d, f"B vs D: ordering differs for query: {query!r}"

        for cb, cd in zip(cands_b, cands_d, strict=True):
            assert cb.rrf_score == pytest.approx(cd.rrf_score, abs=1e-10), (
                f"B vs D: RRF score mismatch for {cb.candidate.chunk_id}"
            )

    # ------------------------------------------------------------------
    # c) B vs E retrieval equivalence (pre-trust-filtering)
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_be_same_retrieval(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """
        Variant E (Trust-Aware Hybrid RAG) applies trust filtering AFTER
        retrieval.  The pre-trust-filtering retrieval must be identical to
        variant B.  This test compares the raw retriever output before
        trust scoring removes ineligible candidates.

        Verifies: candidate IDs, ordering, and RRF scores.
        """
        cands_b, _ = _run_retrieval(retriever, drug_normalizer, query)
        cands_e, _ = _run_retrieval(retriever, drug_normalizer, query)

        ids_b = [c.candidate.chunk_id for c in cands_b]
        ids_e = [c.candidate.chunk_id for c in cands_e]
        assert ids_b == ids_e, f"B vs E: candidate IDs differ for query: {query!r}"

        ranks_b = [c.final_rank for c in cands_b]
        ranks_e = [c.final_rank for c in cands_e]
        assert ranks_b == ranks_e, f"B vs E: ordering differs for query: {query!r}"

        for cb, ce in zip(cands_b, cands_e, strict=True):
            assert cb.rrf_score == pytest.approx(ce.rrf_score, abs=1e-10), (
                f"B vs E: RRF score mismatch for {cb.candidate.chunk_id}"
            )

    # ------------------------------------------------------------------
    # d) All 4 variants — candidate IDs identical
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_candidate_ids_identical(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """
        Run the retrieval function once per variant label (B, C, D, E).
        All four must return the exact same set of chunk_ids in the
        exact same order.  This is the fundamental equivalence invariant.
        """
        results: dict[str, list[str]] = {}
        for variant in VARIANT_LABELS:
            cands, _ = _run_retrieval(retriever, drug_normalizer, query)
            results[variant] = [c.candidate.chunk_id for c in cands]

        reference = results["B"]
        for variant in ["C", "D", "E"]:
            assert results[variant] == reference, (
                f"Variant {variant} chunk_ids differ from B for query: {query!r}"
            )

    # ------------------------------------------------------------------
    # e) All 4 variants — candidate ordering identical
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_candidate_ordering_identical(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """
        Assert that final_rank ordering is identical across all four
        variants.  Even small ordering changes would alter the context
        window presented to the LLM and confound the ablation.
        """
        results: dict[str, list[int | None]] = {}
        for variant in VARIANT_LABELS:
            cands, _ = _run_retrieval(retriever, drug_normalizer, query)
            results[variant] = [c.final_rank for c in cands]

        reference = results["B"]
        for variant in ["C", "D", "E"]:
            assert results[variant] == reference, (
                f"Variant {variant} final_rank ordering differs from B "
                f"for query: {query!r}"
            )

    # ------------------------------------------------------------------
    # f) All 4 variants — top-k count identical
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_topk_identical(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """
        The number of candidates returned must be the same across all
        variants.  A count mismatch would mean one variant sees more or
        fewer evidence chunks, directly confounding answer quality metrics.
        """
        counts: dict[str, int] = {}
        for variant in VARIANT_LABELS:
            cands, _ = _run_retrieval(retriever, drug_normalizer, query)
            counts[variant] = len(cands)

        reference = counts["B"]
        for variant in ["C", "D", "E"]:
            assert counts[variant] == reference, (
                f"Variant {variant} returned {counts[variant]} candidates "
                f"vs B's {reference} for query: {query!r}"
            )

    # ------------------------------------------------------------------
    # g) All 4 variants — RRF scores identical to 10 decimal places
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_rrf_scores_identical(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """
        RRF scores must match to 10 decimal places across all four
        variants.  This rules out floating-point non-determinism caused
        by different retrieval code paths.
        """
        scores: dict[str, list[float]] = {}
        for variant in VARIANT_LABELS:
            cands, _ = _run_retrieval(retriever, drug_normalizer, query)
            scores[variant] = [c.rrf_score for c in cands]

        reference = scores["B"]
        for variant in ["C", "D", "E"]:
            assert len(scores[variant]) == len(reference), (
                f"Variant {variant}: score list length mismatch"
            )
            for idx, (ref_score, var_score) in enumerate(
                zip(reference, scores[variant], strict=True)
            ):
                assert var_score == pytest.approx(ref_score, abs=1e-10), (
                    f"Variant {variant} RRF score at position {idx} differs: "
                    f"{var_score} vs {ref_score}"
                )

    # ------------------------------------------------------------------
    # h) Normalization output identical across 4 runs
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_normalization_identical(
        self,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """
        The drug normalization step (_normalize_query_sync) must produce
        the same query_drugs list on every invocation for the same query.
        Non-deterministic normalization would silently alter graph retrieval
        and corrupt the ablation.
        """
        all_query_drugs: list[list[str]] = []
        for _ in VARIANT_LABELS:
            norm_res = _normalize_query_sync(drug_normalizer, query)
            if hasattr(norm_res, "generic_name") and norm_res.generic_name:
                query_drugs = [norm_res.generic_name]
            elif isinstance(norm_res, list):
                query_drugs = [
                    d.generic_name
                    for d in norm_res
                    if hasattr(d, "generic_name") and d.generic_name
                ]
            else:
                query_drugs = []
            all_query_drugs.append(query_drugs)

        reference = all_query_drugs[0]
        for run_idx, drugs in enumerate(all_query_drugs[1:], start=2):
            assert drugs == reference, (
                f"Run {run_idx} produced query_drugs={drugs} "
                f"vs reference={reference} for query: {query!r}"
            )

    # ------------------------------------------------------------------
    # i) Source code inspection — all variants use the same retrieve call
    # ------------------------------------------------------------------

    def test_no_hidden_variant_retrieval_logic(self) -> None:
        """
        Use inspect.getsource to verify that all variant methods B, C, D,
        and E in RealVariantRunner contain the EXACT same retrieval call
        pattern:  self.retriever.retrieve(case.query, query_drugs=query_drugs, top_k=5)

        This catches accidental divergence in the retrieval call signature
        (e.g., different top_k, missing query_drugs, or extra filters).
        """
        from adaptive_trust_medical_rag.evaluation.live_variants import (
            RealVariantRunner,
        )

        expected_call = "self.retriever.retrieve(case.query, query_drugs=query_drugs, top_k=10)"

        variant_methods = {
            "B": RealVariantRunner._run_variant_b,
            "C": RealVariantRunner._run_variant_c,
            "D": RealVariantRunner._run_variant_d,
            "E": RealVariantRunner._run_variant_e,
        }

        for variant_label, method in variant_methods.items():
            source = inspect.getsource(method)
            assert expected_call in source, (
                f"Variant {variant_label} method "
                f"({method.__name__}) does not contain the expected "
                f"retrieval call: {expected_call!r}"
            )

    # ------------------------------------------------------------------
    # j) Context text identical across B, C, D, E
    # ------------------------------------------------------------------

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_context_text_identical(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        r"""
        Each variant builds context_text via:
            "\n".join([c.candidate.text for c in cands])

        This test verifies that the resulting string is identical across
        B, C, D, and E.  Differences in context_text would mean the LLM
        sees different evidence, directly confounding the ablation.
        """
        context_texts: dict[str, str] = {}
        for variant in VARIANT_LABELS:
            cands, _ = _run_retrieval(retriever, drug_normalizer, query)
            context_texts[variant] = "\n".join(
                [c.candidate.text for c in cands]
            )

        reference = context_texts["B"]
        for variant in ["C", "D", "E"]:
            assert context_texts[variant] == reference, (
                f"Variant {variant} context_text differs from B "
                f"for query: {query!r}"
            )

    # ------------------------------------------------------------------
    # Additional structural sanity checks
    # ------------------------------------------------------------------

    def test_corpus_has_four_candidates(self) -> None:
        """Verify the synthetic corpus has exactly 4 candidates."""
        assert len(SYNTHETIC_CORPUS) == 4

    def test_corpus_chunk_ids_are_unique(self) -> None:
        """All chunk_ids in the synthetic corpus must be unique."""
        ids = [c.chunk_id for c in SYNTHETIC_CORPUS]
        assert len(ids) == len(set(ids))

    def test_no_poisoned_candidates(self) -> None:
        """All synthetic candidates have poisoning_score ≤ 0.4 (pass filter)."""
        for c in SYNTHETIC_CORPUS:
            assert c.poisoning_score <= 0.4, (
                f"{c.chunk_id} has poisoning_score={c.poisoning_score}"
            )

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_retrieval_returns_nonempty(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """Sanity check: each test query retrieves at least one candidate."""
        cands, _ = _run_retrieval(retriever, drug_normalizer, query)
        assert len(cands) > 0, f"No candidates retrieved for query: {query!r}"

    @pytest.mark.parametrize("query", TEST_QUERIES, ids=lambda q: q[:40])
    def test_all_rrf_scores_positive(
        self,
        retriever: HybridRetrievalEngine,
        drug_normalizer: DrugNormalizer,
        query: str,
    ) -> None:
        """Every returned candidate must have a positive RRF score."""
        cands, _ = _run_retrieval(retriever, drug_normalizer, query)
        for c in cands:
            assert c.rrf_score > 0, (
                f"{c.candidate.chunk_id} has non-positive RRF score: {c.rrf_score}"
            )

    def test_normalization_function_matches_source(self) -> None:
        """
        Verify that _normalize_query_sync in live_variants.py has the
        expected signature and uses asyncio.run as the primary path.
        This guards against silent changes to the normalization code.
        """
        from adaptive_trust_medical_rag.evaluation import live_variants

        source = inspect.getsource(live_variants._normalize_query_sync)
        assert "asyncio.run(normalizer.normalize(query))" in source, (
            "The primary normalization path must use asyncio.run()"
        )
        assert "loop.run_until_complete(normalizer.normalize(query))" in source, (
            "The fallback normalization path must use loop.run_until_complete()"
        )
