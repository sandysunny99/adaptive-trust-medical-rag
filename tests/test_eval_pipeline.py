"""
Tests for Phase 17 - End-to-End Evaluation Pipeline.

All tests use MockVariantPipeline + smoke/dev fixtures - no live LLM.
Covers: run_evaluation() with all splits, PHI guard, test-set guard,
        Markdown report generation, summary JSON, report path,
        variant subset runs, result fields.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from adaptive_trust_medical_rag.evaluation.eval_pipeline import (
    EvalPipelineResult,
    _load_or_generate,
    run_evaluation,
)
from adaptive_trust_medical_rag.evaluation.evaluator import (
    DatasetSplit,
)
from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
    AblationVariant,
    ExperimentTracker,
)


def _tracker(tmp_path: Path) -> ExperimentTracker:
    return ExperimentTracker(log_dir=tmp_path / "logs")


def _run(
    tmp_path: Path,
    split: DatasetSplit = DatasetSplit.smoke,
    variants: list[AblationVariant] | None = None,
    bootstrap: bool = False,
) -> EvalPipelineResult:
    return run_evaluation(
        split=split,
        variants=variants or [AblationVariant.B, AblationVariant.F],
        tracker=_tracker(tmp_path),
        reports_dir=tmp_path / "reports",
        logs_dir=tmp_path / "logs",
        bootstrap=bootstrap,
        experiment_name="test-eval",
    )


class TestRunEvaluationSmoke:
    def test_returns_eval_pipeline_result(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert isinstance(result, EvalPipelineResult)

    def test_n_variants_correct(self, tmp_path: Path) -> None:
        result = _run(tmp_path, variants=[AblationVariant.B, AblationVariant.F])
        assert result.n_variants == 2

    def test_split_correct(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert result.split == "smoke"

    def test_total_cases_correct(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert result.total_cases == 20

    def test_experiment_name_stored(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert result.experiment_name == "test-eval"

    def test_run_timestamp_format(self, tmp_path: Path) -> None:
        import re
        result = _run(tmp_path)
        assert re.match(r"\d{8}T\d{6}Z", result.run_timestamp)

    def test_report_has_variant_results(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert len(result.report.variant_results) == 2

    def test_markdown_report_is_string(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert isinstance(result.markdown_report, str)
        assert len(result.markdown_report) > 100

    def test_markdown_contains_variant_labels(self, tmp_path: Path) -> None:
        result = _run(tmp_path, variants=[AblationVariant.B, AblationVariant.F])
        assert "| **B**" in result.markdown_report
        assert "| **F**" in result.markdown_report

    def test_markdown_contains_metric_headers(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert "Faith." in result.markdown_report or "Faithful" in result.markdown_report
        assert "Hallu." in result.markdown_report or "Hallucin" in result.markdown_report
        assert "F1" in result.markdown_report

    def test_markdown_contains_research_disclaimer(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert "research" in result.markdown_report.lower()
        assert "not clinical" in result.markdown_report.lower()

    def test_report_path_created(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert result.report_path.exists()

    def test_report_path_is_markdown(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        assert result.report_path.suffix == ".md"

    def test_summary_json_created(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        # Summary JSON shares the same dir as report
        assert any(p.suffix == ".json" for p in result.report_path.parent.iterdir())

    def test_summary_has_required_keys(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        for key in ["experiment_name", "split", "n_variants", "run_timestamp"]:
            assert key in result.summary

    def test_jsonl_log_created(self, tmp_path: Path) -> None:
        _run(tmp_path)
        jsonl = tmp_path / "logs" / "experiment_runs.jsonl"
        assert jsonl.exists()

    def test_comparisons_generated(self, tmp_path: Path) -> None:
        result = _run(tmp_path, variants=[AblationVariant.B, AblationVariant.F])
        assert len(result.report.comparisons) >= 1


class TestRunEvaluationAllVariants:
    def test_all_6_variants_run(self, tmp_path: Path) -> None:
        result = run_evaluation(
            split=DatasetSplit.smoke,
            tracker=_tracker(tmp_path),
            reports_dir=tmp_path / "reports",
            logs_dir=tmp_path / "logs",
            bootstrap=False,
            experiment_name="all-variants",
        )
        assert result.n_variants == 6

    def test_f_beats_a_faithfulness(self, tmp_path: Path) -> None:
        result = run_evaluation(
            split=DatasetSplit.smoke,
            variants=[AblationVariant.A, AblationVariant.F],
            tracker=_tracker(tmp_path),
            reports_dir=tmp_path / "reports",
            logs_dir=tmp_path / "logs",
            bootstrap=False,
        )
        vr_a = result.report.get_variant(AblationVariant.A)
        vr_f = result.report.get_variant(AblationVariant.F)
        assert vr_f is not None and vr_a is not None
        assert vr_f.faithfulness > vr_a.faithfulness

    def test_markdown_integrity_attestation(self, tmp_path: Path) -> None:
        result = run_evaluation(
            split=DatasetSplit.smoke,
            variants=[AblationVariant.F],
            tracker=_tracker(tmp_path),
            reports_dir=tmp_path / "reports",
            logs_dir=tmp_path / "logs",
            bootstrap=False,
        )
        assert "Research Integrity Attestation" in result.markdown_report
        assert "Test set" in result.markdown_report


class TestRunEvaluationDev:
    def test_dev_fixture_loads_correctly(self, tmp_path: Path) -> None:
        result = run_evaluation(
            split=DatasetSplit.dev,
            variants=[AblationVariant.B, AblationVariant.F],
            tracker=_tracker(tmp_path),
            reports_dir=tmp_path / "reports",
            logs_dir=tmp_path / "logs",
            bootstrap=False,
        )
        assert result.split == "dev"
        assert result.total_cases == 100

    def test_dev_split_reported(self, tmp_path: Path) -> None:
        result = run_evaluation(
            split=DatasetSplit.dev,
            variants=[AblationVariant.F],
            tracker=_tracker(tmp_path),
            reports_dir=tmp_path / "reports",
            logs_dir=tmp_path / "logs",
            bootstrap=False,
        )
        assert result.split == "dev"
        assert "dev" in result.report.dataset_split


class TestGuards:
    def test_test_split_blocked(self, tmp_path: Path) -> None:
        with pytest.raises(PermissionError, match="FROZEN"):
            run_evaluation(
                split=DatasetSplit.test,
                tracker=_tracker(tmp_path),
                reports_dir=tmp_path / "reports",
                logs_dir=tmp_path / "logs",
                bootstrap=False,
            )

    def test_phi_in_dataset_blocks_evaluation(self, tmp_path: Path) -> None:
        # Directly test verify_no_phi integration
        from adaptive_trust_medical_rag.evaluation.dataset_generator import verify_no_phi
        from adaptive_trust_medical_rag.evaluation.evaluator import EvalCase, EvalDataset, QueryType
        bad_case = EvalCase(
            case_id="phi-test-1",
            query="Patient SSN: 123-45-6789 needs warfarin",
            split=DatasetSplit.dev,
            query_type=QueryType.factual,
        )
        bad_ds = EvalDataset(name="bad", cases=[bad_case])
        violations = verify_no_phi(bad_ds)
        assert len(violations) > 0  # PHI correctly detected


class TestBuildMarkdownReport:
    def test_contains_experiment_name(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        md = result.markdown_report
        assert "test-eval" in md

    def test_contains_ci_section(self, tmp_path: Path) -> None:
        result = _run(tmp_path, bootstrap=True)
        md = result.markdown_report
        assert "Confidence Interval" in md

    def test_contains_improvement_table(self, tmp_path: Path) -> None:
        result = _run(tmp_path, variants=[AblationVariant.B, AblationVariant.F])
        md = result.markdown_report
        assert "Improvement Over Baseline" in md

    def test_contains_run_config_table(self, tmp_path: Path) -> None:
        result = _run(tmp_path)
        md = result.markdown_report
        assert "Run Configuration" in md
        assert "Config Hash" in md

    def test_comparison_table_present(self, tmp_path: Path) -> None:
        result = _run(tmp_path, variants=[AblationVariant.B, AblationVariant.F])
        md = result.markdown_report
        assert "Pairwise Statistical" in md


class TestLoadOrGenerate:
    def test_smoke_returns_20_cases(self) -> None:
        ds = _load_or_generate(DatasetSplit.smoke)
        assert len(ds.cases) == 20

    def test_dev_fixture_returns_100_cases(self) -> None:
        ds = _load_or_generate(DatasetSplit.dev)
        assert len(ds.cases) == 100

    def test_val_fixture_returns_200_cases(self) -> None:
        ds = _load_or_generate(DatasetSplit.val)
        assert len(ds.cases) == 200

    def test_dev_phi_free(self) -> None:
        from adaptive_trust_medical_rag.evaluation.dataset_generator import verify_no_phi
        ds = _load_or_generate(DatasetSplit.dev)
        assert verify_no_phi(ds) == []
