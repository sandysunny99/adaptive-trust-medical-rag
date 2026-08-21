"""
Tests for Phase 13 — Evaluation Framework.

All pure-Python with a mock pipeline. No live LLM/DB. No real PHI.
Covers: EvalCase, EvalDataset, EvalMetrics, EvalResult,
        bootstrap CI, paired t-test, RAGEvaluator full run,
        leakage detection, test-set guard, smoke dataset factory.
"""

from __future__ import annotations

import pytest

from adaptive_trust_medical_rag.evaluation.evaluator import (
    BootstrapCI,
    DatasetSplit,
    EvalCase,
    EvalDataset,
    EvalResult,
    QueryType,
    RAGEvaluator,
    _bootstrap_ci,
    make_smoke_dataset,
    paired_ttest,
)
from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import (
    PipelineStatus,
    RAGRequest,
    RAGResponse,
)
from adaptive_trust_medical_rag.verification.claim_verifier import (
    GateDecision,
    VerificationReport,
)

# ---------------------------------------------------------------------------
# Mock pipeline helpers
# ---------------------------------------------------------------------------


def _mock_response(
    status: PipelineStatus = PipelineStatus.released,
    confidence: float = 0.80,
    answer: str = "Warfarin is an anticoagulant [Source 1].",
) -> RAGResponse:
    vr = VerificationReport(
        claims=[],
        alignments=[],
        contradictions=[],
        grounding_ratio=0.85,
        mean_citation_trust=0.90,
        contradiction_score=0.0,
        confidence=confidence,
        decision=GateDecision.release,
        explanation="Test response",
    )
    return RAGResponse(
        session_id="test-session",
        query_hash="abc123",
        risk_tier="R1",
        status=status,
        answer=answer,
        confidence=confidence,
        trust_scores=[0.8],
        retrieved_chunk_ids=["c-001"],
        gate_decision=GateDecision.release.value,
        verification_report=vr,
        audit_log={"steps": []},
    )


def _mock_abstain() -> RAGResponse:
    return _mock_response(
        status=PipelineStatus.abstained,
        confidence=0.0,
        answer="[SYSTEM ABSTENTION]",
    )


class MockPipeline:
    """Configurable mock pipeline for evaluation tests."""

    def __init__(self, always_abstain: bool = False, confidence: float = 0.8) -> None:
        self.always_abstain = always_abstain
        self.confidence = confidence

    def __call__(self, req: RAGRequest) -> RAGResponse:
        if "ignore previous" in req.query.lower() or self.always_abstain:
            return _mock_abstain()
        return _mock_response(confidence=self.confidence)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _make_case(
    query: str = "What is warfarin?",
    split: DatasetSplit = DatasetSplit.smoke,
    query_type: QueryType = QueryType.factual,
    expected_abstain: bool = False,
    expected_drugs: list[str] | None = None,
    risk_tier: str = "R1",
) -> EvalCase:
    return EvalCase.make(
        query=query,
        split=split,
        query_type=query_type,
        expected_abstain=expected_abstain,
        expected_drugs=expected_drugs or [],
        risk_tier=risk_tier,
    )


def _make_dataset(
    n_smoke: int = 20,
    n_dev: int = 0,
    n_val: int = 0,
    n_test: int = 0,
) -> EvalDataset:
    cases: list[EvalCase] = []
    for i in range(n_smoke):
        cases.append(_make_case(query=f"Smoke query {i}"))
    for i in range(n_dev):
        cases.append(_make_case(query=f"Dev query {i}", split=DatasetSplit.dev))
    for i in range(n_val):
        cases.append(_make_case(query=f"Val query {i}", split=DatasetSplit.val))
    for i in range(n_test):
        cases.append(_make_case(query=f"Test query {i}", split=DatasetSplit.test))
    return EvalDataset(name="test-dataset", cases=cases)


# ---------------------------------------------------------------------------
# EvalCase
# ---------------------------------------------------------------------------


class TestEvalCase:
    def test_case_id_is_16_chars(self) -> None:
        assert len(_make_case().case_id) == 16

    def test_case_id_stable(self) -> None:
        assert _make_case(query="warfarin?").case_id == _make_case(query="warfarin?").case_id

    def test_different_queries_different_ids(self) -> None:
        assert _make_case(query="warfarin?").case_id != _make_case(query="metformin?").case_id

    def test_same_query_different_splits_different_ids(self) -> None:
        c1 = _make_case(query="warfarin?", split=DatasetSplit.smoke)
        c2 = _make_case(query="warfarin?", split=DatasetSplit.dev)
        assert c1.case_id != c2.case_id

    def test_expected_drugs_stored(self) -> None:
        c = _make_case(expected_drugs=["warfarin", "aspirin"])
        assert "warfarin" in c.expected_drugs and "aspirin" in c.expected_drugs

    def test_expected_abstain_flag(self) -> None:
        assert _make_case(expected_abstain=True).expected_abstain

    def test_risk_tier_stored(self) -> None:
        assert _make_case(risk_tier="R3").risk_tier == "R3"


# ---------------------------------------------------------------------------
# EvalDataset
# ---------------------------------------------------------------------------


class TestEvalDataset:
    def test_split_counts(self) -> None:
        ds = _make_dataset(n_smoke=20, n_dev=5)
        assert ds.split_counts()["smoke"] == 20
        assert ds.split_counts()["dev"] == 5

    def test_get_split_smoke(self) -> None:
        assert len(_make_dataset(n_smoke=20).get_split(DatasetSplit.smoke)) == 20

    def test_test_split_blocked_by_default(self) -> None:
        with pytest.raises(PermissionError, match="FROZEN"):
            _make_dataset(n_test=5).get_split(DatasetSplit.test)

    def test_test_split_allowed_with_flag(self) -> None:
        assert len(_make_dataset(n_test=5).get_split(DatasetSplit.test, allow_test=True)) == 5

    def test_leakage_detection(self) -> None:
        shared_id = "shared-case-id-x"
        smoke = EvalCase(
            case_id=shared_id, query="q-smoke",
            split=DatasetSplit.smoke, query_type=QueryType.factual,
        )
        test = EvalCase(
            case_id=shared_id, query="q-test",
            split=DatasetSplit.test, query_type=QueryType.factual,
        )
        with pytest.raises(ValueError, match="LEAKAGE"):
            EvalDataset(name="leaky", cases=[smoke, test])

    def test_no_leakage_passes(self) -> None:
        assert _make_dataset(n_smoke=20, n_test=5) is not None

    def test_validate_sizes_below_minimum(self) -> None:
        violations = _make_dataset(n_smoke=3).validate_sizes()
        assert any("smoke" in v for v in violations)


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------


class TestBootstrapCI:
    def test_perfect_scores_ci_near_1(self) -> None:
        ci = _bootstrap_ci([1.0] * 50, n=100)
        assert abs(ci.mean - 1.0) < 1e-6 and ci.lower >= 0.99

    def test_zero_scores_ci_near_0(self) -> None:
        assert abs(_bootstrap_ci([0.0] * 50, n=100).mean) < 1e-6

    def test_ci_lower_le_mean_le_upper(self) -> None:
        import random
        vals = [random.Random(0).random() for _ in range(50)]
        ci = _bootstrap_ci(vals, n=200)
        assert ci.lower <= ci.mean <= ci.upper

    def test_empty_values_returns_zero(self) -> None:
        ci = _bootstrap_ci([])
        assert ci.mean == 0.0 and ci.n_samples == 0

    def test_returns_bootstrap_ci_type(self) -> None:
        assert isinstance(_bootstrap_ci([0.7, 0.8, 0.9], n=100), BootstrapCI)

    def test_wider_ci_for_small_sample(self) -> None:
        import random
        rng = random.Random(42)
        small = [rng.gauss(0.7, 0.1) for _ in range(10)]
        large = [rng.gauss(0.7, 0.1) for _ in range(200)]
        ci_s = _bootstrap_ci(small, n=500)
        ci_l = _bootstrap_ci(large, n=500)
        assert (ci_l.upper - ci_l.lower) < (ci_s.upper - ci_s.lower)


# ---------------------------------------------------------------------------
# Paired t-test
# ---------------------------------------------------------------------------


class TestPairedTtest:
    def test_identical_no_significance(self) -> None:
        assert paired_ttest([0.8] * 30, [0.8] * 30)["p_value"] == 1.0

    def test_clearly_different_significant(self) -> None:
        import random
        rng = random.Random(2)
        a = [0.3 + rng.gauss(0, 0.01) for _ in range(50)]
        b = [0.9 + rng.gauss(0, 0.01) for _ in range(50)]
        result = paired_ttest(a, b)
        assert result["significant"] and result["p_value"] < 0.05

    def test_cohen_d_sign(self) -> None:
        import random
        rng = random.Random(1)
        a = [0.9 + rng.gauss(0, 0.01) for _ in range(30)]
        b = [0.5 + rng.gauss(0, 0.01) for _ in range(30)]
        assert paired_ttest(a, b)["cohen_d"] > 0

    def test_mismatched_lengths_raises(self) -> None:
        with pytest.raises(ValueError):
            paired_ttest([0.8] * 10, [0.9] * 20)

    def test_single_pair_returns_dict(self) -> None:
        r = paired_ttest([0.8], [0.7])
        assert "t_statistic" in r and "p_value" in r


# ---------------------------------------------------------------------------
# Smoke dataset factory
# ---------------------------------------------------------------------------


class TestMakeSmokeDataset:
    def test_returns_20_cases(self) -> None:
        assert len(make_smoke_dataset().cases) == 20

    def test_all_smoke_split(self) -> None:
        assert all(c.split == DatasetSplit.smoke for c in make_smoke_dataset().cases)

    def test_has_injection_cases(self) -> None:
        assert any(c.query_type == QueryType.injection for c in make_smoke_dataset().cases)

    def test_has_factual_cases(self) -> None:
        assert any(c.query_type == QueryType.factual for c in make_smoke_dataset().cases)

    def test_injection_cases_expect_abstain(self) -> None:
        ds = make_smoke_dataset()
        assert all(c.expected_abstain for c in ds.cases if c.query_type == QueryType.injection)

    def test_no_phi_in_queries(self) -> None:
        import re
        phi_patterns = [r"\b\d{3}-\d{2}-\d{4}\b", r"\bMRN\s*#?\d+\b", r"\b\d{10,}\b"]
        for case in make_smoke_dataset().cases:
            for pat in phi_patterns:
                assert not re.search(pat, case.query), f"PHI in {case.case_id}"

    def test_dataset_name_contains_smoke(self) -> None:
        assert "smoke" in make_smoke_dataset().name

    def test_no_leakage(self) -> None:
        assert make_smoke_dataset() is not None


# ---------------------------------------------------------------------------
# RAGEvaluator integration
# ---------------------------------------------------------------------------


class TestRAGEvaluator:
    def _ds(self) -> EvalDataset:
        return make_smoke_dataset()

    def _run(self, pipeline: MockPipeline | None = None, bootstrap: bool = False) -> EvalResult:
        return RAGEvaluator(pipeline or MockPipeline(), "test").evaluate(
            self._ds(), DatasetSplit.smoke, bootstrap=bootstrap
        )

    def test_returns_eval_result(self) -> None:
        assert isinstance(self._run(), EvalResult)

    def test_n_cases_correct(self) -> None:
        assert self._run().n_cases == 20

    def test_metrics_in_range(self) -> None:
        r = self._run()
        for attr in [
            "mean_hallucination_rate", "mean_faithfulness",
            "mean_citation_precision", "mean_citation_recall",
            "mean_entity_attribution_acc", "mean_robustness_score",
        ]:
            val = getattr(r, attr)
            assert 0.0 <= val <= 1.0, f"{attr}={val}"

    def test_f1_abstain_in_range(self) -> None:
        assert 0.0 <= self._run().f1_abstain <= 1.0

    def test_bootstrap_ci_computed(self) -> None:
        r = self._run(bootstrap=True)
        assert r.ci_faithfulness is not None
        assert r.ci_faithfulness.lower <= r.ci_faithfulness.upper

    def test_summary_contains_key_metrics(self) -> None:
        s = self._run().summary()
        assert "Faithfulness" in s and "Hallucination" in s and "F1-Abstain" in s

    def test_compare_returns_ttest(self) -> None:
        ds = self._ds()
        ev_a = RAGEvaluator(MockPipeline(confidence=0.5), "A")
        ev_b = RAGEvaluator(MockPipeline(confidence=0.9), "B")
        r_a = ev_a.evaluate(ds, DatasetSplit.smoke, bootstrap=False)
        r_b = ev_b.evaluate(ds, DatasetSplit.smoke, bootstrap=False)
        comp = ev_a.compare(r_a, r_b, metric="pipeline_confidence")
        assert "t_statistic" in comp and "p_value" in comp and "significant" in comp

    def test_test_split_blocked(self) -> None:
        with pytest.raises(PermissionError, match="FROZEN"):
            RAGEvaluator(MockPipeline(), "t").evaluate(
                _make_dataset(n_test=5), DatasetSplit.test
            )

    def test_errors_counted(self) -> None:
        def broken(_: RAGRequest) -> RAGResponse:
            raise RuntimeError("LLM down")
        r = RAGEvaluator(broken, "broken").evaluate(self._ds(), DatasetSplit.smoke)
        assert r.n_errors == 20

    def test_experiment_name_stored(self) -> None:
        r = RAGEvaluator(MockPipeline(), "my-exp").evaluate(
            self._ds(), DatasetSplit.smoke
        )
        assert r.experiment_name == "my-exp"

    def test_timestamp_set(self) -> None:
        assert self._run().evaluated_at is not None

    def test_robustness_1_for_factual_queries(self) -> None:
        factual = [c for c in self._ds().cases if c.query_type == QueryType.factual]
        ds = EvalDataset(name="factual-only", cases=factual)
        r = RAGEvaluator(MockPipeline(), "t").evaluate(ds, DatasetSplit.smoke)
        assert r.mean_robustness_score == 1.0

    def test_always_abstain_scores_perfectly_on_abstain_cases(self) -> None:
        abstain_cases = [c for c in self._ds().cases if c.expected_abstain]
        ds = EvalDataset(name="abstain-only", cases=abstain_cases)
        r = RAGEvaluator(MockPipeline(always_abstain=True), "t").evaluate(
            ds, DatasetSplit.smoke
        )
        assert r.f1_abstain == 1.0
