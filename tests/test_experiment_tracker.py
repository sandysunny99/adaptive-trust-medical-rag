"""
Tests for Phase 14 - MLflow Experiment Tracker.

All tests use JSONL fallback (mlflow not installed in dev/CI).
Covers: ExperimentConfig hash, AblationVariant, MetricSnapshot,
        ExperimentTracker (log/load/compare), make_experiment_config.
"""

from __future__ import annotations

from pathlib import Path

from adaptive_trust_medical_rag.evaluation.evaluator import (
    DatasetSplit,
    EvalResult,
    RAGEvaluator,
    make_smoke_dataset,
)
from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
    ABLATION_DESCRIPTIONS,
    DEFAULT_TRUST_WEIGHTS,
    AblationVariant,
    ExperimentConfig,
    ExperimentTracker,
    MetricSnapshot,
    make_experiment_config,
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


def _mock_response(confidence: float = 0.8) -> RAGResponse:
    vr = VerificationReport(
        claims=[], alignments=[], contradictions=[],
        grounding_ratio=0.85, mean_citation_trust=0.90,
        contradiction_score=0.0, confidence=confidence,
        decision=GateDecision.release, explanation="test",
    )
    return RAGResponse(
        session_id="s1", query_hash="h1", risk_tier="R1",
        status=PipelineStatus.released, answer="ans [Source 1].",
        confidence=confidence, trust_scores=[0.8],
        retrieved_chunk_ids=["c1"], gate_decision=GateDecision.release.value,
        verification_report=vr, audit_log={},
    )


class MockPipeline:
    def __call__(self, req: RAGRequest) -> RAGResponse:
        return _mock_response()


def _make_result(experiment_name: str = "test-exp") -> EvalResult:
    ds = make_smoke_dataset()
    return RAGEvaluator(MockPipeline(), experiment_name).evaluate(
        ds, DatasetSplit.smoke, bootstrap=True
    )


def _make_config(variant: AblationVariant = AblationVariant.F) -> ExperimentConfig:
    return make_experiment_config(
        model_name="test-model",
        ablation_variant=variant,
        dataset_name="smoke-synthetic-v1",
        dataset_split="smoke",
    )


def _make_tracker(tmp_path: Path) -> ExperimentTracker:
    return ExperimentTracker(
        experiment_name="test-exp",
        log_dir=tmp_path / "logs",
    )


class TestAblationVariant:
    def test_all_six_variants_exist(self) -> None:
        variants = list(AblationVariant)
        assert len(variants) == 6

    def test_variant_values(self) -> None:
        assert AblationVariant.A.value == "A"
        assert AblationVariant.F.value == "F"

    def test_all_variants_have_descriptions(self) -> None:
        for v in AblationVariant:
            assert v.value in ABLATION_DESCRIPTIONS

    def test_descriptions_are_non_empty(self) -> None:
        for desc in ABLATION_DESCRIPTIONS.values():
            assert len(desc) > 0

    def test_f_is_full_architecture(self) -> None:
        assert "full" in ABLATION_DESCRIPTIONS["F"].lower() or \
               "dual" in ABLATION_DESCRIPTIONS["F"].lower()


class TestExperimentConfig:
    def test_hash_is_16_chars(self) -> None:
        cfg = _make_config()
        assert len(cfg.compute_hash()) == 16

    def test_hash_is_hex(self) -> None:
        cfg = _make_config()
        int(cfg.compute_hash(), 16)  # raises if not valid hex

    def test_same_config_same_hash(self) -> None:
        cfg1 = _make_config()
        cfg2 = _make_config()
        assert cfg1.compute_hash() == cfg2.compute_hash()

    def test_different_model_different_hash(self) -> None:
        cfg1 = make_experiment_config("model-a", AblationVariant.F, "ds")
        cfg2 = make_experiment_config("model-b", AblationVariant.F, "ds")
        assert cfg1.compute_hash() != cfg2.compute_hash()

    def test_different_variant_different_hash(self) -> None:
        cfg1 = make_experiment_config("m", AblationVariant.A, "ds")
        cfg2 = make_experiment_config("m", AblationVariant.F, "ds")
        assert cfg1.compute_hash() != cfg2.compute_hash()

    def test_different_weights_different_hash(self) -> None:
        w1 = {"authority": 0.30, "freshness": 0.15, "entity_match": 0.20,
               "consistency": 0.15, "anti_poisoning": 0.20}
        w2 = {"authority": 0.50, "freshness": 0.10, "entity_match": 0.15,
               "consistency": 0.15, "anti_poisoning": 0.10}
        cfg1 = make_experiment_config("m", AblationVariant.F, "ds", trust_weights=w1)
        cfg2 = make_experiment_config("m", AblationVariant.F, "ds", trust_weights=w2)
        assert cfg1.compute_hash() != cfg2.compute_hash()

    def test_to_mlflow_params_has_config_hash(self) -> None:
        cfg = _make_config()
        params = cfg.to_mlflow_params()
        assert "config_hash" in params
        assert params["config_hash"] == cfg.compute_hash()

    def test_to_mlflow_params_has_all_keys(self) -> None:
        cfg = _make_config()
        params = cfg.to_mlflow_params()
        for key in ["model_name", "model_temperature", "dataset_name",
                    "dataset_split", "ablation_variant", "prompt_version"]:
            assert key in params

    def test_trust_weights_in_params(self) -> None:
        cfg = _make_config()
        params = cfg.to_mlflow_params()
        assert "trust_weight_authority" in params


class TestMetricSnapshot:
    def test_to_mlflow_metrics_has_all_7(self) -> None:
        snap = MetricSnapshot(
            run_id="r1", experiment_name="e", config_hash="h",
            ablation_variant="F", dataset_split="smoke",
            n_cases=20, n_errors=0, evaluated_at="2026-01-01T00:00:00",
            mean_hallucination_rate=0.1, mean_faithfulness=0.9,
            mean_citation_precision=0.85, mean_citation_recall=0.80,
            mean_entity_attribution_acc=0.95, mean_robustness_score=1.0,
            f1_abstain=0.75,
        )
        metrics = snap.to_mlflow_metrics()
        for key in ["hallucination_rate", "faithfulness", "citation_precision",
                    "citation_recall", "entity_attribution_acc",
                    "robustness_score", "f1_abstain"]:
            assert key in metrics

    def test_ci_bounds_in_metrics(self) -> None:
        snap = MetricSnapshot(
            run_id="r1", experiment_name="e", config_hash="h",
            ablation_variant="F", dataset_split="smoke",
            n_cases=20, n_errors=0, evaluated_at="2026-01-01T00:00:00",
            mean_hallucination_rate=0.1, mean_faithfulness=0.9,
            mean_citation_precision=0.85, mean_citation_recall=0.80,
            mean_entity_attribution_acc=0.95, mean_robustness_score=1.0,
            f1_abstain=0.75,
            ci_faithfulness_lower=0.85, ci_faithfulness_upper=0.95,
        )
        metrics = snap.to_mlflow_metrics()
        assert "ci_faithfulness_lower" in metrics
        assert "ci_faithfulness_upper" in metrics

    def test_n_cases_in_metrics(self) -> None:
        snap = MetricSnapshot(
            run_id="r", experiment_name="e", config_hash="h",
            ablation_variant="F", dataset_split="smoke",
            n_cases=20, n_errors=2, evaluated_at="2026-01-01T00:00:00",
            mean_hallucination_rate=0.0, mean_faithfulness=1.0,
            mean_citation_precision=1.0, mean_citation_recall=1.0,
            mean_entity_attribution_acc=1.0, mean_robustness_score=1.0,
            f1_abstain=1.0,
        )
        metrics = snap.to_mlflow_metrics()
        assert metrics["n_cases"] == 20.0
        assert metrics["n_errors"] == 2.0


class TestExperimentTracker:
    def test_mlflow_not_available_in_ci(self, tmp_path: Path) -> None:
        tracker = _make_tracker(tmp_path)
        # mlflow is not installed in dev/CI env
        assert not tracker.mlflow_available

    def test_experiment_name_stored(self, tmp_path: Path) -> None:
        tracker = ExperimentTracker(
            experiment_name="my-exp", log_dir=tmp_path / "logs"
        )
        assert tracker.experiment_name == "my-exp"

    def test_log_eval_result_returns_run_id(self, tmp_path: Path) -> None:
        tracker = _make_tracker(tmp_path)
        result = _make_result()
        config = _make_config()
        run_id = tracker.log_eval_result(result, config)
        assert isinstance(run_id, str) and len(run_id) > 0

    def test_log_creates_jsonl_file(self, tmp_path: Path) -> None:
        tracker = _make_tracker(tmp_path)
        tracker.log_eval_result(_make_result(), _make_config())
        jsonl = tmp_path / "logs" / "experiment_runs.jsonl"
        assert jsonl.exists()

    def test_logged_run_has_config_hash(self, tmp_path: Path) -> None:
        tracker = _make_tracker(tmp_path)
        config = _make_config()
        tracker.log_eval_result(_make_result(), config)
        history = tracker.load_run_history()
        assert len(history) == 1
        assert history[0]["params"]["config_hash"] == config.compute_hash()

    def test_logged_run_has_all_metrics(self, tmp_path: Path) -> None:
        tracker = _make_tracker(tmp_path)
        tracker.log_eval_result(_make_result(), _make_config())
        history = tracker.load_run_history()
        metrics = history[0]["metrics"]
        for key in ["hallucination_rate", "faithfulness", "citation_precision",
                    "citation_recall", "entity_attribution_acc",
                    "robustness_score", "f1_abstain"]:
            assert key in metrics

    def test_multiple_runs_appended(self, tmp_path: Path) -> None:
        tracker = _make_tracker(tmp_path)
        for variant in [AblationVariant.A, AblationVariant.B, AblationVariant.F]:
            tracker.log_eval_result(_make_result(), _make_config(variant))
        history = tracker.load_run_history()
        assert len(history) == 3

    def test_different_configs_different_hashes(self, tmp_path: Path) -> None:
        tracker = _make_tracker(tmp_path)
        tracker.log_eval_result(_make_result(), _make_config(AblationVariant.A))
        tracker.log_eval_result(_make_result(), _make_config(AblationVariant.F))
        history = tracker.load_run_history()
        hashes = [h["params"]["config_hash"] for h in history]
        assert hashes[0] != hashes[1]

    def test_load_run_history_empty_initially(self, tmp_path: Path) -> None:
        tracker = _make_tracker(tmp_path)
        assert tracker.load_run_history() == []

    def test_log_comparison_appends_to_jsonl(self, tmp_path: Path) -> None:
        tracker = _make_tracker(tmp_path)
        run_id = tracker.log_eval_result(_make_result(), _make_config())
        tracker.log_comparison(
            parent_run_id=run_id,
            comparison={"t_statistic": 3.5, "p_value": 0.001, "significant": True,
                        "cohen_d": 1.2, "n": 20, "mean_a": 0.7, "mean_b": 0.9},
            variant_a="B",
            variant_b="F",
            metric="faithfulness",
        )
        history = tracker.load_run_history()
        assert len(history) == 2
        comp = history[1]
        assert comp["type"] == "comparison"
        assert comp["comparison"]["variant_a"] == "B"
        assert comp["comparison"]["variant_b"] == "F"

    def test_run_id_is_uuid_format(self, tmp_path: Path) -> None:
        import re
        tracker = _make_tracker(tmp_path)
        run_id = tracker.log_eval_result(_make_result(), _make_config())
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        assert re.match(uuid_pattern, run_id), f"Not UUID format: {run_id}"

    def test_no_phi_in_logged_records(self, tmp_path: Path) -> None:
        """Privacy check: logged records must not contain raw query text."""
        tracker = _make_tracker(tmp_path)
        tracker.log_eval_result(_make_result("ablation-exp"), _make_config())
        jsonl = tmp_path / "logs" / "experiment_runs.jsonl"
        content = jsonl.read_text()
        # Should not contain any actual query strings
        assert "What is warfarin" not in content
        assert "ignore previous" not in content


class TestMakeExperimentConfig:
    def test_returns_experiment_config(self) -> None:
        cfg = make_experiment_config("m", AblationVariant.F, "ds")
        assert isinstance(cfg, ExperimentConfig)

    def test_default_trust_weights_applied(self) -> None:
        cfg = make_experiment_config("m", AblationVariant.F, "ds")
        assert cfg.trust_weights == DEFAULT_TRUST_WEIGHTS

    def test_custom_trust_weights(self) -> None:
        w = {"authority": 0.5, "freshness": 0.1, "entity_match": 0.2,
             "consistency": 0.1, "anti_poisoning": 0.1}
        cfg = make_experiment_config("m", AblationVariant.F, "ds", trust_weights=w)
        assert cfg.trust_weights["authority"] == 0.5

    def test_retriever_config_stored(self) -> None:
        cfg = make_experiment_config("m", AblationVariant.F, "ds", k=10, rrf_k=60)
        assert cfg.retriever_config["k"] == 10
        assert cfg.retriever_config["rrf_k"] == 60

    def test_temperature_stored(self) -> None:
        cfg = make_experiment_config("m", AblationVariant.F, "ds", temperature=0.7)
        assert cfg.model_temperature == 0.7

    def test_hash_deterministic_across_calls(self) -> None:
        h1 = make_experiment_config("m", AblationVariant.F, "ds").compute_hash()
        h2 = make_experiment_config("m", AblationVariant.F, "ds").compute_hash()
        assert h1 == h2
