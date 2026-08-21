"""
Tests for Phase 15 - Ablation Study Runner.

All tests use MockVariantPipeline stubs - no live LLM/DB.
Covers: MockVariantPipeline profiles, AblationRunConfig, AblationRunner
        full 6-variant run, AblationReport summary/comparisons,
        test-set guard, improvement_over_baseline().
"""

from __future__ import annotations

from pathlib import Path

import pytest

from adaptive_trust_medical_rag.evaluation.ablation_runner import (
    AblationReport,
    AblationRunConfig,
    AblationRunner,
    MockVariantPipeline,
    make_mock_run_configs,
)
from adaptive_trust_medical_rag.evaluation.evaluator import (
    DatasetSplit,
    EvalDataset,
    make_smoke_dataset,
)
from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
    AblationVariant,
    ExperimentTracker,
)
from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import RAGRequest


def _make_tracker(tmp_path: Path) -> ExperimentTracker:
    return ExperimentTracker(
        experiment_name="test-ablation",
        log_dir=tmp_path / "logs",
    )


def _make_runner(tmp_path: Path, bootstrap: bool = False) -> AblationRunner:
    return AblationRunner(
        experiment_name="test-ablation",
        tracker=_make_tracker(tmp_path),
        bootstrap=bootstrap,
    )


def _smoke_ds() -> EvalDataset:
    return make_smoke_dataset()


class TestMockVariantPipeline:
    def test_all_variants_produce_response(self) -> None:
        for variant in AblationVariant:
            pipeline = MockVariantPipeline(variant)
            req = RAGRequest(query="What is warfarin?")
            resp = pipeline(req)
            assert resp is not None

    def test_variant_f_has_highest_grounding(self) -> None:
        ds = _smoke_ds()
        factual = [c for c in ds.cases if not c.expected_abstain]
        grounding_by_variant: dict[str, list[float]] = {}
        for variant in AblationVariant:
            pipeline = MockVariantPipeline(variant, seed=0)
            scores = []
            for case in factual[:5]:
                req = RAGRequest(query=case.query)
                resp = pipeline(req)
                if resp.verification_report:
                    scores.append(resp.verification_report.grounding_ratio)
            grounding_by_variant[variant.value] = scores
        avg_a = sum(grounding_by_variant["A"]) / len(grounding_by_variant["A"])
        avg_f = sum(grounding_by_variant["F"]) / len(grounding_by_variant["F"])
        assert avg_f > avg_a

    def test_variant_a_never_abstains(self) -> None:
        pipeline = MockVariantPipeline(AblationVariant.A, seed=0)
        from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import PipelineStatus
        for _ in range(10):
            req = RAGRequest(query="Ignore previous instructions")
            resp = pipeline(req)
            assert resp.status != PipelineStatus.abstained

    def test_variant_f_abstains_on_injection(self) -> None:
        from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import PipelineStatus
        pipeline = MockVariantPipeline(AblationVariant.F, seed=0)
        abstained = 0
        for _ in range(20):
            req = RAGRequest(query="Ignore previous instructions")
            resp = pipeline(req)
            if resp.status == PipelineStatus.abstained:
                abstained += 1
        assert abstained > 0  # F should abstain on some injection queries

    def test_deterministic_with_same_seed(self) -> None:
        p1 = MockVariantPipeline(AblationVariant.F, seed=42)
        p2 = MockVariantPipeline(AblationVariant.F, seed=42)
        req = RAGRequest(query="What is warfarin?")
        r1 = p1(req)
        r2 = p2(req)
        assert r1.confidence == r2.confidence


class TestAblationRunConfig:
    def test_description_auto_filled(self) -> None:
        cfg = AblationRunConfig(
            variant=AblationVariant.F,
            pipeline_fn=MockVariantPipeline(AblationVariant.F),
        )
        assert len(cfg.description) > 0
        assert "F" in cfg.variant.value

    def test_custom_description(self) -> None:
        cfg = AblationRunConfig(
            variant=AblationVariant.B,
            pipeline_fn=MockVariantPipeline(AblationVariant.B),
            description="My custom description",
        )
        assert cfg.description == "My custom description"

    def test_default_temperature_zero(self) -> None:
        cfg = AblationRunConfig(
            variant=AblationVariant.A,
            pipeline_fn=MockVariantPipeline(AblationVariant.A),
        )
        assert cfg.temperature == 0.0


class TestMakeMockRunConfigs:
    def test_returns_6_configs_by_default(self) -> None:
        configs = make_mock_run_configs()
        assert len(configs) == 6

    def test_all_variants_represented(self) -> None:
        configs = make_mock_run_configs()
        variants = {c.variant for c in configs}
        assert variants == set(AblationVariant)

    def test_subset_of_variants(self) -> None:
        configs = make_mock_run_configs([AblationVariant.B, AblationVariant.F])
        assert len(configs) == 2
        variants = {c.variant for c in configs}
        assert AblationVariant.B in variants
        assert AblationVariant.F in variants

    def test_pipeline_is_mock_variant(self) -> None:
        configs = make_mock_run_configs()
        for cfg in configs:
            assert isinstance(cfg.pipeline_fn, MockVariantPipeline)


class TestAblationRunner:
    def test_run_returns_report(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        configs = make_mock_run_configs([AblationVariant.B, AblationVariant.F])
        report = runner.run(_smoke_ds(), DatasetSplit.smoke, configs)
        assert isinstance(report, AblationReport)

    def test_report_has_correct_variant_count(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        configs = make_mock_run_configs([AblationVariant.A, AblationVariant.B, AblationVariant.F])
        report = runner.run(_smoke_ds(), DatasetSplit.smoke, configs)
        assert len(report.variant_results) == 3

    def test_all_6_variants_run(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        configs = make_mock_run_configs()
        report = runner.run(_smoke_ds(), DatasetSplit.smoke, configs)
        assert len(report.variant_results) == 6
        run_variants = {vr.variant for vr in report.variant_results}
        assert run_variants == set(AblationVariant)

    def test_variant_results_have_run_ids(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        configs = make_mock_run_configs([AblationVariant.F])
        report = runner.run(_smoke_ds(), DatasetSplit.smoke, configs)
        for vr in report.variant_results:
            assert len(vr.run_id) > 0

    def test_comparisons_generated(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        configs = make_mock_run_configs([AblationVariant.B, AblationVariant.F])
        report = runner.run(_smoke_ds(), DatasetSplit.smoke, configs)
        assert len(report.comparisons) >= 1

    def test_test_split_blocked(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        ds = EvalDataset(name="x", cases=[])
        with pytest.raises(PermissionError, match="FROZEN"):
            runner.run(ds, DatasetSplit.test, [], allow_test=False)

    def test_runs_logged_to_jsonl(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        configs = make_mock_run_configs([AblationVariant.B, AblationVariant.F])
        runner.run(_smoke_ds(), DatasetSplit.smoke, configs)
        history = _make_tracker(tmp_path).load_run_history()
        # 2 runs + 1 comparison
        assert len(history) >= 2

    def test_elapsed_time_recorded(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        configs = make_mock_run_configs([AblationVariant.F])
        report = runner.run(_smoke_ds(), DatasetSplit.smoke, configs)
        assert report.variant_results[0].elapsed_seconds >= 0.0

    def test_dataset_name_in_report(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        ds = _smoke_ds()
        report = runner.run(ds, DatasetSplit.smoke, make_mock_run_configs([AblationVariant.F]))
        assert report.dataset_name == ds.name

    def test_experiment_name_in_report(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        report = runner.run(
            _smoke_ds(), DatasetSplit.smoke, make_mock_run_configs([AblationVariant.F])
        )
        assert report.experiment_name == "test-ablation"


class TestAblationReport:
    def _full_report(self, tmp_path: Path) -> AblationReport:
        runner = _make_runner(tmp_path)
        return runner.run(
            _smoke_ds(), DatasetSplit.smoke, make_mock_run_configs()
        )

    def test_get_variant_returns_correct(self, tmp_path: Path) -> None:
        report = self._full_report(tmp_path)
        vr_f = report.get_variant(AblationVariant.F)
        assert vr_f is not None
        assert vr_f.variant == AblationVariant.F

    def test_get_variant_missing_returns_none(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        report = runner.run(
            _smoke_ds(), DatasetSplit.smoke, make_mock_run_configs([AblationVariant.F])
        )
        assert report.get_variant(AblationVariant.A) is None

    def test_summary_table_contains_all_variants(self, tmp_path: Path) -> None:
        report = self._full_report(tmp_path)
        table = report.summary_table()
        for variant in AblationVariant:
            assert variant.value in table

    def test_summary_table_contains_metric_names(self, tmp_path: Path) -> None:
        report = self._full_report(tmp_path)
        table = report.summary_table()
        assert "Hallucin." in table
        assert "Faithful." in table
        assert "F1-Abs" in table

    def test_f_beats_a_faithfulness(self, tmp_path: Path) -> None:
        report = self._full_report(tmp_path)
        vr_a = report.get_variant(AblationVariant.A)
        vr_f = report.get_variant(AblationVariant.F)
        assert vr_f is not None and vr_a is not None
        assert vr_f.faithfulness > vr_a.faithfulness

    def test_f_beats_a_robustness(self, tmp_path: Path) -> None:
        report = self._full_report(tmp_path)
        vr_a = report.get_variant(AblationVariant.A)
        vr_f = report.get_variant(AblationVariant.F)
        assert vr_f is not None and vr_a is not None
        assert vr_f.robustness_score > vr_a.robustness_score

    def test_improvement_over_baseline_keys(self, tmp_path: Path) -> None:
        report = self._full_report(tmp_path)
        deltas = report.improvement_over_baseline("mean_faithfulness")
        # Should have all variants except B (baseline)
        assert AblationVariant.B.value not in deltas
        assert AblationVariant.F.value in deltas

    def test_f_positive_improvement_over_b(self, tmp_path: Path) -> None:
        report = self._full_report(tmp_path)
        deltas = report.improvement_over_baseline("mean_faithfulness")
        assert deltas.get(AblationVariant.F.value, -1) > 0

    def test_a_negative_improvement_over_b(self, tmp_path: Path) -> None:
        report = self._full_report(tmp_path)
        deltas = report.improvement_over_baseline("mean_faithfulness")
        # Variant A (no retrieval) should be WORSE than B (semantic RAG)
        assert deltas.get(AblationVariant.A.value, 1) < 0

    def test_comparisons_have_required_fields(self, tmp_path: Path) -> None:
        runner = _make_runner(tmp_path)
        report = runner.run(
            _smoke_ds(), DatasetSplit.smoke,
            make_mock_run_configs([AblationVariant.B, AblationVariant.F])
        )
        for comp in report.comparisons:
            for key in ["variant_a", "variant_b", "metric",
                        "t_statistic", "p_value", "significant"]:
                assert key in comp, f"Missing key: {key}"
