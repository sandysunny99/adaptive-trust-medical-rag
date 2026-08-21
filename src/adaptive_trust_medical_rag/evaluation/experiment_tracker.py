"""
Phase 14 - MLflow Experiment Tracker.

Records every evaluation run with full reproducibility metadata
per the medical-rag-evaluation skill requirements:

  - Complete parameter sets: model, temperature, trust_weights,
    dataset_version, timestamp, config_hash
  - All 7 core metrics with 95% bootstrap CIs
  - Ablation variant tags (A/B/C/D/E/F per skill Ablation Study Matrix)
  - Paired comparison results logged as child runs
  - MLflow optional: gracefully degrades to JSON file logging
    when mlflow is not installed (for CI/lightweight envs)

Privacy rule: Only metric scores and config hashes are logged.
              NEVER log raw queries, answers, or any PHI.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)


class AblationVariant(str, Enum):
    """
    Six pipeline configurations for the ablation study.
    Matches the medical-rag-evaluation skill Ablation Study Matrix exactly.
    """
    A = "A"  # Baseline: Vanilla LLM (direct prompting, no retrieval)
    B = "B"  # Baseline: Standard Semantic RAG (dense vector, no trust, no gates)
    C = "C"  # Ablation: BM25 + Vector Hybrid Retrieval (no trust scoring)
    D = "D"  # Ablation: Hybrid + Adaptive Trust Scoring (pre-gen gate only)
    E = "E"  # Ablation: Full Pipeline without Post-Generation Answer Safety Gate
    F = "F"  # Full Architecture: End-to-end Trust-Aware RAG + Dual Gates


ABLATION_DESCRIPTIONS: dict[str, str] = {
    "A": "Vanilla LLM - direct prompting, no retrieval",
    "B": "Standard Semantic RAG - dense vector, no trust, no gates",
    "C": "Hybrid Retrieval (BM25+Vector) - no trust scoring",
    "D": "Hybrid + Adaptive Trust - pre-generation gate only",
    "E": "Full Pipeline - without Post-Generation Answer Safety Gate",
    "F": "Full Architecture - dual gates, entity attribution, trust",
}

DEFAULT_TRUST_WEIGHTS: dict[str, float] = {
    "authority": 0.30,
    "freshness": 0.15,
    "entity_match": 0.20,
    "consistency": 0.15,
    "anti_poisoning": 0.20,
}


@dataclass
class ExperimentConfig:
    """
    Complete experiment configuration - hashed for reproducibility.

    Every distinct configuration produces a unique config_hash.
    This hash is logged alongside metrics to enable exact reproduction.
    """

    model_name: str
    model_temperature: float
    trust_weights: dict[str, float]
    dataset_name: str
    dataset_version: str
    dataset_split: str
    ablation_variant: str
    prompt_version: str = "v1.0"
    retriever_config: dict[str, Any] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def compute_hash(self) -> str:
        """
        Compute a deterministic SHA-256 hash of all config parameters.
        Used as a reproducibility key in every logged run.
        """
        payload = {
            "model_name": self.model_name,
            "model_temperature": self.model_temperature,
            "trust_weights": dict(sorted(self.trust_weights.items())),
            "dataset_name": self.dataset_name,
            "dataset_version": self.dataset_version,
            "dataset_split": self.dataset_split,
            "ablation_variant": self.ablation_variant,
            "prompt_version": self.prompt_version,
            "retriever_config": dict(sorted(self.retriever_config.items())),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode()).hexdigest()[:16]

    def to_mlflow_params(self) -> dict[str, str]:
        """Flatten config to MLflow-compatible string params."""
        return {
            "model_name": self.model_name,
            "model_temperature": str(self.model_temperature),
            "dataset_name": self.dataset_name,
            "dataset_version": self.dataset_version,
            "dataset_split": self.dataset_split,
            "ablation_variant": self.ablation_variant,
            "ablation_description": ABLATION_DESCRIPTIONS.get(
                self.ablation_variant, "custom"
            ),
            "prompt_version": self.prompt_version,
            "config_hash": self.compute_hash(),
            **{f"trust_weight_{k}": str(v) for k, v in self.trust_weights.items()},
            **{f"retriever_{k}": str(v) for k, v in self.retriever_config.items()},
        }


@dataclass
class MetricSnapshot:
    """
    Complete snapshot of one evaluation run metrics - what gets persisted.

    Privacy: only aggregated numeric scores + hashes. No raw text, no PHI.
    """

    run_id: str
    experiment_name: str
    config_hash: str
    ablation_variant: str
    dataset_split: str
    n_cases: int
    n_errors: int
    evaluated_at: str

    # Core metrics (mean)
    mean_hallucination_rate: float
    mean_faithfulness: float
    mean_citation_precision: float
    mean_citation_recall: float
    mean_entity_attribution_acc: float
    mean_robustness_score: float
    f1_abstain: float

    # Bootstrap 95% CIs
    ci_hallucination_lower: float = 0.0
    ci_hallucination_upper: float = 0.0
    ci_faithfulness_lower: float = 0.0
    ci_faithfulness_upper: float = 0.0
    ci_citation_precision_lower: float = 0.0
    ci_citation_precision_upper: float = 0.0
    ci_citation_recall_lower: float = 0.0
    ci_citation_recall_upper: float = 0.0
    ci_entity_attribution_lower: float = 0.0
    ci_entity_attribution_upper: float = 0.0
    ci_robustness_lower: float = 0.0
    ci_robustness_upper: float = 0.0

    def to_mlflow_metrics(self) -> dict[str, float]:
        """Flatten to MLflow metric key->float dict."""
        return {
            "hallucination_rate": self.mean_hallucination_rate,
            "faithfulness": self.mean_faithfulness,
            "citation_precision": self.mean_citation_precision,
            "citation_recall": self.mean_citation_recall,
            "entity_attribution_acc": self.mean_entity_attribution_acc,
            "robustness_score": self.mean_robustness_score,
            "f1_abstain": self.f1_abstain,
            "n_cases": float(self.n_cases),
            "n_errors": float(self.n_errors),
            "ci_hallucination_lower": self.ci_hallucination_lower,
            "ci_hallucination_upper": self.ci_hallucination_upper,
            "ci_faithfulness_lower": self.ci_faithfulness_lower,
            "ci_faithfulness_upper": self.ci_faithfulness_upper,
            "ci_citation_precision_lower": self.ci_citation_precision_lower,
            "ci_citation_precision_upper": self.ci_citation_precision_upper,
            "ci_citation_recall_lower": self.ci_citation_recall_lower,
            "ci_citation_recall_upper": self.ci_citation_recall_upper,
            "ci_entity_attribution_lower": self.ci_entity_attribution_lower,
            "ci_entity_attribution_upper": self.ci_entity_attribution_upper,
            "ci_robustness_lower": self.ci_robustness_lower,
            "ci_robustness_upper": self.ci_robustness_upper,
        }


class _JsonFileLogger:
    """Fallback: appends experiment snapshots to a JSONL file."""

    def __init__(self, log_dir: Path) -> None:
        self._path = log_dir / "experiment_runs.jsonl"
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def log_run(self, snapshot: MetricSnapshot, params: dict[str, str]) -> str:
        record = {
            "run_id": snapshot.run_id,
            "params": params,
            "metrics": snapshot.to_mlflow_metrics(),
            "logged_at": datetime.now(UTC).isoformat(),
        }
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        log.info("Experiment run logged to %s (run_id=%s)", self._path, snapshot.run_id)
        return snapshot.run_id

    def log_comparison(self, parent_run_id: str, comparison: dict[str, Any]) -> None:
        record = {
            "type": "comparison",
            "parent_run_id": parent_run_id,
            "comparison": comparison,
            "logged_at": datetime.now(UTC).isoformat(),
        }
        with self._path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    def load_history(self) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        runs = []
        with self._path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        runs.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return runs


class ExperimentTracker:
    """
    Logs evaluation experiment runs to MLflow (primary) or JSONL (fallback).

    Usage::

        config = make_experiment_config(
            model_name="gpt-4o-mini",
            ablation_variant=AblationVariant.F,
            dataset_name="smoke-synthetic-v1",
        )
        tracker = ExperimentTracker(experiment_name="ablation-study-1")
        run_id = tracker.log_eval_result(result, config)
    """

    _DEFAULT_TRACKING_URI = "mlruns"

    def __init__(
        self,
        experiment_name: str = "adaptive-trust-medical-rag",
        tracking_uri: str | None = None,
        log_dir: Path | None = None,
    ) -> None:
        self._experiment_name = experiment_name
        self._tracking_uri = (
            tracking_uri
            or os.environ.get("MLFLOW_TRACKING_URI")
            or self._DEFAULT_TRACKING_URI
        )
        self._log_dir = log_dir or Path("experiments") / "logs"
        self._mlflow_available = self._check_mlflow()
        self._fallback = _JsonFileLogger(self._log_dir)

        if self._mlflow_available:
            import mlflow  # type: ignore[import-untyped]
            mlflow.set_tracking_uri(self._tracking_uri)
            mlflow.set_experiment(self._experiment_name)
            log.info(
                "ExperimentTracker: MLflow active at %s (experiment=%s)",
                self._tracking_uri,
                self._experiment_name,
            )
        else:
            log.warning(
                "ExperimentTracker: MLflow not available - using JSONL fallback at %s",
                self._log_dir,
            )

    def log_eval_result(
        self,
        result: Any,
        config: ExperimentConfig,
    ) -> str:
        """
        Log a complete EvalResult to MLflow or JSONL fallback.

        Privacy: Only metric scores and config hashes are logged.
                 Raw queries, answers, and PHI are NEVER persisted.

        Returns:
            run_id string (MLflow UUID or local UUID).
        """
        snapshot = self._build_snapshot(result, config)
        params = config.to_mlflow_params()

        if self._mlflow_available:
            return self._log_to_mlflow(snapshot, params)
        return self._fallback.log_run(snapshot, params)

    def log_comparison(
        self,
        parent_run_id: str,
        comparison: dict[str, Any],
        variant_a: str,
        variant_b: str,
        metric: str,
    ) -> None:
        """Log a paired t-test comparison between two ablation variants."""
        record = {
            "parent_run_id": parent_run_id,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "metric": metric,
            **comparison,
        }
        if self._mlflow_available:
            self._log_comparison_to_mlflow(parent_run_id, record)
        else:
            self._fallback.log_comparison(parent_run_id, record)

    def load_run_history(self) -> list[dict[str, Any]]:
        """Load all runs from JSONL fallback. Returns [] when MLflow is used."""
        return self._fallback.load_history()

    @property
    def mlflow_available(self) -> bool:
        return self._mlflow_available

    @property
    def experiment_name(self) -> str:
        return self._experiment_name

    @staticmethod
    def _check_mlflow() -> bool:
        try:
            import mlflow  # type: ignore[import-untyped]  # noqa: F401
            return True
        except ImportError:
            return False

    @staticmethod
    def _build_snapshot(result: Any, config: ExperimentConfig) -> MetricSnapshot:
        def _lo(ci: Any) -> float:
            return ci.lower if ci is not None else 0.0

        def _hi(ci: Any) -> float:
            return ci.upper if ci is not None else 0.0

        return MetricSnapshot(
            run_id=str(uuid.uuid4()),
            experiment_name=result.experiment_name,
            config_hash=config.compute_hash(),
            ablation_variant=config.ablation_variant,
            dataset_split=result.split,
            n_cases=result.n_cases,
            n_errors=result.n_errors,
            evaluated_at=result.evaluated_at.isoformat(),
            mean_hallucination_rate=result.mean_hallucination_rate,
            mean_faithfulness=result.mean_faithfulness,
            mean_citation_precision=result.mean_citation_precision,
            mean_citation_recall=result.mean_citation_recall,
            mean_entity_attribution_acc=result.mean_entity_attribution_acc,
            mean_robustness_score=result.mean_robustness_score,
            f1_abstain=result.f1_abstain,
            ci_hallucination_lower=_lo(result.ci_hallucination_rate),
            ci_hallucination_upper=_hi(result.ci_hallucination_rate),
            ci_faithfulness_lower=_lo(result.ci_faithfulness),
            ci_faithfulness_upper=_hi(result.ci_faithfulness),
            ci_citation_precision_lower=_lo(result.ci_citation_precision),
            ci_citation_precision_upper=_hi(result.ci_citation_precision),
            ci_citation_recall_lower=_lo(result.ci_citation_recall),
            ci_citation_recall_upper=_hi(result.ci_citation_recall),
            ci_entity_attribution_lower=_lo(result.ci_entity_attribution_acc),
            ci_entity_attribution_upper=_hi(result.ci_entity_attribution_acc),
            ci_robustness_lower=_lo(result.ci_robustness_score),
            ci_robustness_upper=_hi(result.ci_robustness_score),
        )

    def _log_to_mlflow(
        self, snapshot: MetricSnapshot, params: dict[str, str]
    ) -> str:
        import mlflow  # type: ignore[import-untyped]

        with mlflow.start_run(run_name=snapshot.experiment_name) as run:
            mlflow.set_tags({
                "ablation_variant": snapshot.ablation_variant,
                "config_hash": snapshot.config_hash,
                "dataset_split": snapshot.dataset_split,
            })
            mlflow.log_params(params)
            mlflow.log_metrics(snapshot.to_mlflow_metrics())
            run_id = run.info.run_id
            log.info("MLflow run logged: %s", run_id)
            return run_id

    def _log_comparison_to_mlflow(
        self, parent_run_id: str, record: dict[str, Any]
    ) -> None:
        import mlflow  # type: ignore[import-untyped]

        with mlflow.start_run(
            run_name=f"comparison_{record.get('metric', 'metric')}",
            nested=True,
            tags={"parent_run_id": parent_run_id, "type": "paired_comparison"},
        ):
            mlflow.log_metrics({
                k: float(v)
                for k, v in record.items()
                if isinstance(v, (int, float))
            })
            mlflow.log_params({
                k: str(v)
                for k, v in record.items()
                if isinstance(v, (str, bool))
            })


def make_experiment_config(
    model_name: str,
    ablation_variant: AblationVariant,
    dataset_name: str,
    dataset_version: str = "1.0",
    dataset_split: str = "smoke",
    temperature: float = 0.0,
    trust_weights: dict[str, float] | None = None,
    prompt_version: str = "v1.0",
    **retriever_config: Any,
) -> ExperimentConfig:
    """
    Convenience factory for ExperimentConfig with sensible defaults.

    Args:
        model_name:       LLM identifier (e.g. "gpt-4o-mini").
        ablation_variant: Which ablation variant (A-F).
        dataset_name:     Dataset identifier string.
        dataset_version:  Dataset version string.
        dataset_split:    Split evaluated (smoke/dev/val/test).
        temperature:      LLM temperature (0.0 for deterministic).
        trust_weights:    Override default trust weight dict.
        prompt_version:   Prompt template version string.
        retriever_config: Arbitrary retriever parameters (k, rrf_k, etc.).
    """
    return ExperimentConfig(
        model_name=model_name,
        model_temperature=temperature,
        trust_weights=trust_weights or DEFAULT_TRUST_WEIGHTS.copy(),
        dataset_name=dataset_name,
        dataset_version=dataset_version,
        dataset_split=dataset_split,
        ablation_variant=ablation_variant.value,
        prompt_version=prompt_version,
        retriever_config=dict(retriever_config),
    )
