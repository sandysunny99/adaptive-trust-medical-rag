"""Evaluation package for adaptive-trust-medical-rag."""

from adaptive_trust_medical_rag.evaluation.ablation_runner import (
    AblationReport,
    AblationRunConfig,
    AblationRunner,
    MockVariantPipeline,
    make_mock_run_configs,
)
from adaptive_trust_medical_rag.evaluation.evaluator import (
    BOOTSTRAP_N,
    CI_LEVEL,
    MIN_DEV,
    MIN_SMOKE,
    MIN_TEST,
    MIN_VAL,
    BootstrapCI,
    DatasetSplit,
    EvalCase,
    EvalDataset,
    EvalMetrics,
    EvalResult,
    QueryType,
    RAGEvaluator,
    make_smoke_dataset,
    paired_ttest,
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

__all__ = [
    # ablation_runner
    "AblationReport",
    "AblationRunConfig",
    "AblationRunner",
    "MockVariantPipeline",
    "make_mock_run_configs",
    # evaluator
    "BOOTSTRAP_N",
    "CI_LEVEL",
    "MIN_DEV",
    "MIN_SMOKE",
    "MIN_TEST",
    "MIN_VAL",
    "BootstrapCI",
    "DatasetSplit",
    "EvalCase",
    "EvalDataset",
    "EvalMetrics",
    "EvalResult",
    "QueryType",
    "RAGEvaluator",
    "make_smoke_dataset",
    "paired_ttest",
    # experiment_tracker
    "ABLATION_DESCRIPTIONS",
    "DEFAULT_TRUST_WEIGHTS",
    "AblationVariant",
    "ExperimentConfig",
    "ExperimentTracker",
    "MetricSnapshot",
    "make_experiment_config",
]
