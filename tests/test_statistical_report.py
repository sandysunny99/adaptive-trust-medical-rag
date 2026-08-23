"""
Tests for Phase 22 - Statistical Research Report Generator (statistical_report.py).
"""
from __future__ import annotations

from pathlib import Path

import pytest

from adaptive_trust_medical_rag.evaluation.ablation_runner import (
    AblationReport,
    AblationRunner,
    AblationVariant,
    make_mock_run_configs,
)
from adaptive_trust_medical_rag.evaluation.evaluator import DatasetSplit, make_smoke_dataset
from adaptive_trust_medical_rag.evaluation.experiment_tracker import ExperimentTracker
from adaptive_trust_medical_rag.evaluation.statistical_report import (
    ALL_METRICS,
    DISCLAIMER,
    RESEARCH_INTEGRITY_STATEMENT,
    MetricRanking,
    PairwiseComparison,
    StatisticalReport,
    _cohens_d,
    _welch_t_approx,
    generate_statistical_report,
)


@pytest.fixture
def smoke_ablation_report(tmp_path: Path) -> AblationReport:
    ds = make_smoke_dataset()
    variants = [AblationVariant.A, AblationVariant.B, AblationVariant.F]
    configs = make_mock_run_configs(variants, seed=42)
    tracker = ExperimentTracker(log_dir=tmp_path / "logs")
    runner = AblationRunner(tracker)
    return runner.run(ds, DatasetSplit.smoke, configs)


class TestStatisticalReportGenerator:
    def test_generate_report_basic(
        self, smoke_ablation_report: AblationReport, tmp_path: Path
    ) -> None:
        out_file = tmp_path / "stat_report.md"
        report = generate_statistical_report(
            smoke_ablation_report,
            bootstrap_n=500,
            output_path=out_file,
        )

        assert isinstance(report, StatisticalReport)
        assert report.experiment_name == smoke_ablation_report.experiment_name
        assert report.dataset_split == "smoke"
        assert report.n_cases == 20
        assert report.n_variants == 3
        assert report.bootstrap_n == 500
        assert len(report.variant_names) == 3
        assert out_file.exists()
        assert out_file.stat().st_size > 0

    def test_pairwise_comparisons_computed(self, smoke_ablation_report: AblationReport) -> None:
        report = generate_statistical_report(smoke_ablation_report)
        # Baseline A vs B and F -> 2 pairs * 7 metrics = 14 comparisons
        assert len(report.pairwise) == 14
        for comp in report.pairwise:
            assert isinstance(comp, PairwiseComparison)
            assert comp.variant_a == "A"
            assert comp.variant_b in ("B", "F")
            assert comp.metric in ALL_METRICS
            assert 0.0 <= comp.p_value <= 1.0

    def test_per_metric_rankings(self, smoke_ablation_report: AblationReport) -> None:
        report = generate_statistical_report(smoke_ablation_report)
        assert len(report.rankings) == len(ALL_METRICS)
        for rk in report.rankings:
            assert isinstance(rk, MetricRanking)
            assert rk.metric in ALL_METRICS
            assert len(rk.ranked_variants) == 3

    def test_as_markdown_contains_sections(self, smoke_ablation_report: AblationReport) -> None:
        report = generate_statistical_report(smoke_ablation_report)
        md = report.as_markdown(smoke_ablation_report)

        assert "# Adaptive Trust Medical RAG - Ablation Statistical Report" in md
        assert "## 1. Executive Summary" in md
        assert "## 2. Full Ablation Results" in md
        assert "## 3. Bootstrap Confidence Intervals" in md
        assert "## 4. Pairwise Statistical Tests" in md
        assert "## 5. Per-Metric Rankings" in md
        assert "## 6. Key Statistical Findings" in md
        assert "## 7. Research Integrity Attestation" in md
        assert DISCLAIMER in md
        assert RESEARCH_INTEGRITY_STATEMENT in md

    def test_custom_baseline(self, smoke_ablation_report: AblationReport) -> None:
        report = generate_statistical_report(
            smoke_ablation_report,
            baseline_variant=AblationVariant.B,
        )
        assert all(comp.variant_a == "B" for comp in report.pairwise)

    def test_empty_ablation_report_raises(self) -> None:
        empty_report = AblationReport(
            experiment_name="empty",
            dataset_name="empty",
            dataset_split="smoke",
            variant_results=[],
            comparisons=[],
        )
        with pytest.raises(ValueError, match="AblationReport has no variant results"):
            generate_statistical_report(empty_report)


class TestStatisticalHelpers:
    def test_cohens_d(self) -> None:
        d, category = _cohens_d(0.5, 0.9, 100)
        assert d > 0
        assert category in ("negligible", "small", "medium", "large")

    def test_welch_t_approx(self) -> None:
        p_val, sig = _welch_t_approx(0.5, 0.9, 100, 100)
        assert p_val < 0.05
        assert sig is True

        p_val_equal, sig_equal = _welch_t_approx(0.5, 0.5, 100, 100)
        assert p_val_equal == 1.0
        assert sig_equal is False
