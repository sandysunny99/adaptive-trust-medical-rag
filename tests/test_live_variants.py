# Unit and Integration Tests for Real Live Variant Pipeline Execution

from __future__ import annotations

import pytest

from adaptive_trust_medical_rag.evaluation.evaluator import DatasetSplit, EvalCase, QueryType
from adaptive_trust_medical_rag.evaluation.experiment_tracker import AblationVariant
from adaptive_trust_medical_rag.evaluation.live_variants import RealVariantRunner


@pytest.fixture
def sample_case() -> EvalCase:
    return EvalCase(
        case_id="test-case-001",
        query="What is the mechanism of action of metformin?",
        split=DatasetSplit.smoke,
        query_type=QueryType.factual,
        expected_answer="Metformin decreases hepatic glucose production.",
        risk_tier="R1",
    )


class TestRealLiveVariantExecution:
    def test_live_mode_has_no_mock_dependencies(self, sample_case: EvalCase) -> None:
        runner = RealVariantRunner()
        res = runner.run_case(sample_case, AblationVariant.F)
        assert res.execution_backend == "real_rag_pipeline"
        assert res.runtime_verified is True

    def test_live_variant_A_uses_real_llm(self, sample_case: EvalCase) -> None:
        runner = RealVariantRunner()
        res = runner.run_case(sample_case, AblationVariant.A)
        assert res.variant == "A"
        assert res.llm_execution["called"] is True
        assert res.retrieval_execution["dense_called"] is False

    def test_live_variant_B_uses_dense_retrieval(self, sample_case: EvalCase) -> None:
        runner = RealVariantRunner()
        res = runner.run_case(sample_case, AblationVariant.B)
        assert res.variant == "B"
        assert res.retrieval_execution["dense_called"] is True
        assert res.retrieval_execution["bm25_called"] is False

    def test_live_variant_C_uses_bm25_and_dense(self, sample_case: EvalCase) -> None:
        runner = RealVariantRunner()
        res = runner.run_case(sample_case, AblationVariant.C)
        assert res.variant == "C"
        assert res.retrieval_execution["dense_called"] is True
        assert res.retrieval_execution["bm25_called"] is True
        assert res.retrieval_execution["rrf_called"] is True

    def test_live_variant_D_uses_entity_normalization(self, sample_case: EvalCase) -> None:
        runner = RealVariantRunner()
        res = runner.run_case(sample_case, AblationVariant.D)
        assert res.variant == "D"
        assert res.retrieval_execution["graph_called"] is True

    def test_live_variant_E_uses_trust_scoring(self, sample_case: EvalCase) -> None:
        runner = RealVariantRunner()
        res = runner.run_case(sample_case, AblationVariant.E)
        assert res.variant == "E"
        assert res.trust_execution["called"] is True
        assert "authority" in res.trust_execution["weights"]

    def test_live_variant_F_uses_all_security_gates(self, sample_case: EvalCase) -> None:
        runner = RealVariantRunner()
        res = runner.run_case(sample_case, AblationVariant.F)
        assert res.variant == "F"
        assert res.trust_execution["called"] is True
        assert res.verification_execution["called"] is True

    def test_live_results_have_real_provenance(self, sample_case: EvalCase) -> None:
        runner = RealVariantRunner()
        res = runner.run_case(sample_case, AblationVariant.F)
        d = res.to_dict()
        assert d["execution_backend"] == "real_rag_pipeline"
        assert d["runtime_verified"] is True
        assert len(d["query_hash"]) == 64
