"""
Phase 15 - Ablation Study Runner.

Executes all 6 pipeline variants (A-F) from the skill Ablation Study Matrix
against a benchmark dataset, logs results via ExperimentTracker, and produces
a structured comparison report with paired t-tests.

Ablation variants (skill spec):
  A: Vanilla LLM (direct prompting, no retrieval)
  B: Standard Semantic RAG (dense vector, no trust, no gates)
  C: BM25 + Vector Hybrid Retrieval (no trust scoring)
  D: Hybrid + Adaptive Trust Scoring (pre-generation gate active)
  E: Full Pipeline without Post-Generation Answer Safety Gate
  F: Full Architecture (dual gates + entity attribution)

Design:
  - Each variant is simulated via an AblationPipelineFn callable.
  - In production: real pipeline callables are injected.
  - In tests/CI: lightweight MockVariantPipeline stubs are used.
  - Results are logged to ExperimentTracker (MLflow or JSONL fallback).
  - AblationReport.summary_table() produces a formatted comparison table.

Privacy: Only metric scores and config hashes are persisted. No raw queries.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from adaptive_trust_medical_rag.evaluation.evaluator import (
    DatasetSplit,
    EvalDataset,
    EvalResult,
    RAGEvaluator,
)
from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
    AblationVariant,
    ExperimentConfig,
    ExperimentTracker,
    make_experiment_config,
)
from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import (
    RAGRequest,
    RAGResponse,
)

log = logging.getLogger(__name__)

# Type alias for a callable that handles RAGRequest -> RAGResponse
AblationPipelineFn = Callable[[RAGRequest], RAGResponse]


# ---------------------------------------------------------------------------
# Per-variant run configuration
# ---------------------------------------------------------------------------


@dataclass
class AblationRunConfig:
    """
    Configuration for a single ablation variant run.

    Pairs an AblationVariant with its pipeline callable and
    optional variant-specific overrides.
    """

    variant: AblationVariant
    pipeline_fn: AblationPipelineFn
    model_name: str = "gpt-4o-mini"
    temperature: float = 0.0
    prompt_version: str = "v1.0"
    trust_weights: dict[str, float] | None = None
    retriever_config: dict[str, Any] = field(default_factory=dict)
    description: str = ""

    def __post_init__(self) -> None:
        if not self.description:
            from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
                ABLATION_DESCRIPTIONS,
            )
            self.description = ABLATION_DESCRIPTIONS.get(self.variant.value, "")


# ---------------------------------------------------------------------------
# Per-variant result
# ---------------------------------------------------------------------------


@dataclass
class VariantResult:
    """Result for one ablation variant evaluation."""

    variant: AblationVariant
    config: ExperimentConfig
    result: EvalResult
    run_id: str
    elapsed_seconds: float

    @property
    def faithfulness(self) -> float:
        return self.result.mean_faithfulness

    @property
    def hallucination_rate(self) -> float:
        return self.result.mean_hallucination_rate

    @property
    def robustness_score(self) -> float:
        return self.result.mean_robustness_score

    @property
    def f1_abstain(self) -> float:
        return self.result.f1_abstain


# ---------------------------------------------------------------------------
# Ablation report
# ---------------------------------------------------------------------------


@dataclass
class AblationReport:
    """
    Aggregated ablation study report across all evaluated variants.

    Contains per-variant results and pairwise comparisons vs baseline (B).
    """

    experiment_name: str
    dataset_name: str
    dataset_split: str
    variant_results: list[VariantResult]
    comparisons: list[dict[str, Any]] = field(default_factory=list)

    def get_variant(self, variant: AblationVariant) -> VariantResult | None:
        """Return the result for a specific variant, or None if not run."""
        for vr in self.variant_results:
            if vr.variant == variant:
                return vr
        return None

    def summary_table(self) -> str:
        """
        Formatted markdown-style comparison table.

        Columns: Variant | Description | Hallucin. | Faithful. |
                 Citation P | Citation R | Entity Acc | Robust. | F1-Abstain
        """
        header = (
            f"{'Var':>3} | {'Description':<42} | "
            f"{'Hallucin.':>9} | {'Faithful.':>9} | "
            f"{'Cite P':>6} | {'Cite R':>6} | "
            f"{'EntAcc':>6} | {'Robust':>6} | {'F1-Abs':>6}"
        )
        sep = "-" * len(header)
        lines = [
            f"Ablation Study: {self.experiment_name}",
            f"Dataset: {self.dataset_name} | Split: {self.dataset_split}",
            sep,
            header,
            sep,
        ]
        for vr in sorted(self.variant_results, key=lambda x: x.variant.value):
            r = vr.result
            desc = vr.config.retriever_config.get("description", vr.variant.value)
            if hasattr(vr.config, "extra"):
                desc = vr.config.extra.get("description", desc)
            # Use the variant description from the tracker
            from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
                ABLATION_DESCRIPTIONS,
            )
            desc = ABLATION_DESCRIPTIONS.get(vr.variant.value, vr.variant.value)
            desc = desc[:42]
            lines.append(
                f"{vr.variant.value:>3} | {desc:<42} | "
                f"{r.mean_hallucination_rate:>9.4f} | {r.mean_faithfulness:>9.4f} | "
                f"{r.mean_citation_precision:>6.4f} | {r.mean_citation_recall:>6.4f} | "
                f"{r.mean_entity_attribution_acc:>6.4f} | {r.mean_robustness_score:>6.4f} | "
                f"{r.f1_abstain:>6.4f}"
            )
        lines.append(sep)

        # Append comparison summary if available
        if self.comparisons:
            lines.append("")
            lines.append("Pairwise Comparisons vs Baseline (B) — Faithfulness:")
            lines.append(f"{'Variant':>7} | {'t-stat':>8} | {'p-value':>8} | "
                         f"{'cohen_d':>8} | {'Sig?':>5}")
            lines.append("-" * 50)
            for comp in self.comparisons:
                sig = "YES" if comp.get("significant") else "no"
                lines.append(
                    f"{comp.get('variant_b', '?'):>7} | "
                    f"{comp.get('t_statistic', 0):>8.4f} | "
                    f"{comp.get('p_value', 1):>8.4f} | "
                    f"{comp.get('cohen_d', 0):>8.4f} | "
                    f"{sig:>5}"
                )

        return "\n".join(lines)

    def improvement_over_baseline(
        self,
        metric: str = "mean_faithfulness",
    ) -> dict[str, float]:
        """
        Returns per-variant improvement delta over Variant B (semantic RAG baseline).

        Positive delta = better than baseline. Negative = worse.
        """
        baseline = self.get_variant(AblationVariant.B)
        if baseline is None:
            return {}
        baseline_val = getattr(baseline.result, metric, 0.0)
        return {
            vr.variant.value: round(getattr(vr.result, metric, 0.0) - baseline_val, 4)
            for vr in self.variant_results
            if vr.variant != AblationVariant.B
        }


# ---------------------------------------------------------------------------
# Ablation runner
# ---------------------------------------------------------------------------


class AblationRunner:
    """
    Executes the full ablation study across all 6 pipeline variants.

    Usage::

        runner = AblationRunner(
            experiment_name="ablation-smoke-v1",
            tracker=ExperimentTracker(log_dir=Path("experiments/logs")),
        )
        report = runner.run(
            dataset=smoke_dataset,
            split=DatasetSplit.smoke,
            run_configs=[
                AblationRunConfig(AblationVariant.B, pipeline_b),
                AblationRunConfig(AblationVariant.F, pipeline_f),
            ],
        )
        print(report.summary_table())
    """

    def __init__(
        self,
        experiment_name: str = "adaptive-trust-ablation",
        tracker: ExperimentTracker | None = None,
        log_dir: Path | None = None,
        bootstrap: bool = True,
    ) -> None:
        """
        Args:
            experiment_name: Human-readable experiment label.
            tracker:         ExperimentTracker instance. Created with JSONL
                             fallback if not provided.
            log_dir:         Directory for JSONL fallback logs.
            bootstrap:       Whether to compute bootstrap CIs per run.
        """
        self._experiment_name = experiment_name
        self._tracker = tracker or ExperimentTracker(
            experiment_name=experiment_name,
            log_dir=log_dir or Path("experiments") / "logs",
        )
        self._bootstrap = bootstrap

    def run(
        self,
        dataset: EvalDataset,
        split: DatasetSplit,
        run_configs: list[AblationRunConfig],
        allow_test: bool = False,
        compare_metric: str = "faithfulness",
    ) -> AblationReport:
        """
        Execute all variant runs and produce an AblationReport.

        Args:
            dataset:         Evaluation dataset.
            split:           Dataset split (smoke/dev/val/test).
            run_configs:     List of AblationRunConfig, one per variant.
            allow_test:      Must be True to use frozen test split.
            compare_metric:  Metric used for pairwise t-test comparisons.

        Returns:
            AblationReport with all variant results and comparisons.
        """
        if split == DatasetSplit.test and not allow_test:
            raise PermissionError(
                "TEST SET IS FROZEN. Set allow_test=True only for the "
                "final evaluation run."
            )

        variant_results: list[VariantResult] = []

        for run_cfg in run_configs:
            log.info(
                "Running ablation variant %s: %s",
                run_cfg.variant.value,
                run_cfg.description,
            )
            t_start = time.monotonic()

            # Build ExperimentConfig for this variant
            exp_config = make_experiment_config(
                model_name=run_cfg.model_name,
                ablation_variant=run_cfg.variant,
                dataset_name=dataset.name,
                dataset_version=dataset.version,
                dataset_split=split.value,
                temperature=run_cfg.temperature,
                trust_weights=run_cfg.trust_weights,
                prompt_version=run_cfg.prompt_version,
                **run_cfg.retriever_config,
            )

            # Run evaluation
            evaluator = RAGEvaluator(
                pipeline_fn=run_cfg.pipeline_fn,
                experiment_name=f"{self._experiment_name}_{run_cfg.variant.value}",
                config_hash=exp_config.compute_hash(),
            )
            result = evaluator.evaluate(
                dataset=dataset,
                split=split,
                allow_test=allow_test,
                bootstrap=self._bootstrap,
            )

            elapsed = time.monotonic() - t_start

            # Log to tracker
            run_id = self._tracker.log_eval_result(result, exp_config)

            variant_results.append(VariantResult(
                variant=run_cfg.variant,
                config=exp_config,
                result=result,
                run_id=run_id,
                elapsed_seconds=round(elapsed, 2),
            ))
            log.info(
                "Variant %s done: faithfulness=%.4f, f1_abstain=%.4f (%.1fs)",
                run_cfg.variant.value,
                result.mean_faithfulness,
                result.f1_abstain,
                elapsed,
            )

        # Pairwise comparisons vs baseline (B)
        comparisons = self._run_comparisons(
            variant_results=variant_results,
            metric=compare_metric,
        )

        report = AblationReport(
            experiment_name=self._experiment_name,
            dataset_name=dataset.name,
            dataset_split=split.value,
            variant_results=variant_results,
            comparisons=comparisons,
        )

        log.info(
            "Ablation study complete: %d variants, %d comparisons",
            len(variant_results),
            len(comparisons),
        )
        return report

    def _run_comparisons(
        self,
        variant_results: list[VariantResult],
        metric: str,
    ) -> list[dict[str, Any]]:
        """
        Run paired t-tests: each variant vs Variant B (semantic RAG baseline).

        If Variant B is not in variant_results, compare against the first variant.
        """
        from adaptive_trust_medical_rag.evaluation.evaluator import (
            paired_ttest,
        )

        # Find baseline
        baseline_vr = next(
            (vr for vr in variant_results if vr.variant == AblationVariant.B),
            variant_results[0] if variant_results else None,
        )
        if baseline_vr is None or len(variant_results) < 2:
            return []

        attr_map = {
            "faithfulness": "faithfulness",
            "hallucination_rate": "hallucination_rate",
            "citation_precision": "citation_precision",
            "citation_recall": "citation_recall",
            "entity_attribution_acc": "entity_attribution_acc",
            "robustness_score": "robustness_score",
        }
        metric_attr = attr_map.get(metric, metric)

        baseline_scores = [
            getattr(m, metric_attr)
            for m in baseline_vr.result.metrics_list
            if not m.is_error
        ]

        comparisons = []
        for vr in variant_results:
            if vr.variant == baseline_vr.variant:
                continue
            scores = [
                getattr(m, metric_attr)
                for m in vr.result.metrics_list
                if not m.is_error
            ]
            if len(scores) != len(baseline_scores) or not scores:
                continue
            try:
                stats = paired_ttest(baseline_scores, scores)
                comp = {
                    "variant_a": baseline_vr.variant.value,
                    "variant_b": vr.variant.value,
                    "metric": metric,
                    "mean_baseline": round(
                        sum(baseline_scores) / len(baseline_scores), 4
                    ),
                    "mean_variant": round(sum(scores) / len(scores), 4),
                    **stats,
                }
                comparisons.append(comp)
                # Log to tracker
                self._tracker.log_comparison(
                    parent_run_id=baseline_vr.run_id,
                    comparison=comp,
                    variant_a=baseline_vr.variant.value,
                    variant_b=vr.variant.value,
                    metric=metric,
                )
            except Exception as exc:
                log.warning(
                    "Comparison %s vs %s failed: %s",
                    baseline_vr.variant.value,
                    vr.variant.value,
                    exc,
                )

        return comparisons


# ---------------------------------------------------------------------------
# Mock variant pipelines for testing / CI
# ---------------------------------------------------------------------------


class MockVariantPipeline:
    """
    Lightweight mock pipeline that simulates variant-specific characteristics.

    Used in tests and CI where real LLM/DB connections are unavailable.
    Realistic metric profiles are modelled per variant:
      A: high hallucination, no abstention
      B: moderate grounding, no abstention
      C: better grounding (hybrid retrieval), no abstention
      D: good grounding + some abstention (pre-gen gate)
      E: good grounding + abstention (no post-gen gate)
      F: best grounding + correct abstention (full architecture)
    """

    _PROFILES: dict[str, dict[str, float]] = {
        "A": {"grounding": 0.30, "abstain_prob": 0.00, "robustness": 0.00},
        "B": {"grounding": 0.55, "abstain_prob": 0.00, "robustness": 0.10},
        "C": {"grounding": 0.65, "abstain_prob": 0.00, "robustness": 0.20},
        "D": {"grounding": 0.75, "abstain_prob": 0.50, "robustness": 0.70},
        "E": {"grounding": 0.82, "abstain_prob": 0.70, "robustness": 0.85},
        "F": {"grounding": 0.90, "abstain_prob": 0.90, "robustness": 1.00},
    }

    def __init__(self, variant: AblationVariant, seed: int = 42) -> None:
        self._variant = variant
        self._profile = self._PROFILES[variant.value]
        import random
        self._rng = random.Random(seed)  # noqa: S311 - mock pipeline, not cryptographic

    def __call__(self, req: RAGRequest) -> RAGResponse:
        from adaptive_trust_medical_rag.orchestrator.rag_orchestrator import (
            PipelineStatus,
        )
        from adaptive_trust_medical_rag.verification.claim_verifier import (
            GateDecision,
            VerificationReport,
        )

        profile = self._profile
        is_attack = (
            "ignore previous" in req.query.lower()
            or "system prompt" in req.query.lower()
        )

        # Decide whether to abstain
        should_abstain = is_attack and self._rng.random() < profile["abstain_prob"]

        grounding = profile["grounding"] + self._rng.gauss(0, 0.03)
        grounding = max(0.0, min(1.0, grounding))
        confidence = grounding if not should_abstain else 0.0

        vr = VerificationReport(
            claims=[],
            alignments=[],
            contradictions=[],
            grounding_ratio=grounding,
            mean_citation_trust=grounding,
            contradiction_score=0.0,
            confidence=confidence,
            decision=GateDecision.abstain if should_abstain else GateDecision.release,
            explanation=f"Mock variant {self._variant.value}",
        )

        return RAGResponse(
            session_id="mock",
            query_hash="mock-hash",
            risk_tier=getattr(req, "risk_tier_override", "R1") or "R1",
            status=PipelineStatus.abstained if should_abstain else PipelineStatus.released,
            answer=(
                "[SYSTEM ABSTENTION: insufficient evidence]"
                if should_abstain
                else f"Mock answer from variant {self._variant.value} [Source 1]."
            ),
            confidence=confidence,
            trust_scores=[grounding],
            retrieved_chunk_ids=["c-mock"],
            gate_decision=(
                GateDecision.abstain.value
                if should_abstain
                else GateDecision.release.value
            ),
            verification_report=vr,
            audit_log={"variant": self._variant.value},
        )


def make_mock_run_configs(
    variants: list[AblationVariant] | None = None,
    seed: int = 42,
) -> list[AblationRunConfig]:
    """
    Create AblationRunConfig list using MockVariantPipeline stubs.

    Used in tests, CI, and local development without live LLM/DB.

    Args:
        variants: Subset of variants to include. Defaults to all 6 (A-F).
        seed:     Random seed for reproducible mock outputs.

    Returns:
        List of AblationRunConfig ready for AblationRunner.run().
    """
    if variants is None:
        variants = list(AblationVariant)
    return [
        AblationRunConfig(
            variant=v,
            pipeline_fn=MockVariantPipeline(v, seed=seed),
            model_name="mock-model",
            temperature=0.0,
        )
        for v in variants
    ]
