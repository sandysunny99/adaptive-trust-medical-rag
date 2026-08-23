#!/usr/bin/env python
"""CI: Run full 6-variant ablation on 100-case dev dataset (main only)."""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from adaptive_trust_medical_rag.evaluation.eval_pipeline import run_evaluation
from adaptive_trust_medical_rag.evaluation.evaluator import DatasetSplit
from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
    AblationVariant,
    ExperimentTracker,
)

reports_dir = Path("ci-reports/dev")
logs_dir = Path("ci-reports/logs")
reports_dir.mkdir(parents=True, exist_ok=True)
logs_dir.mkdir(parents=True, exist_ok=True)

result = run_evaluation(
    split=DatasetSplit.dev,
    tracker=ExperimentTracker(experiment_name="ci-dev", log_dir=logs_dir),
    reports_dir=reports_dir,
    logs_dir=logs_dir,
    bootstrap=True,
    experiment_name="ci-dev-ablation",
)

vr_f = result.report.get_variant(AblationVariant.F)
vr_a = result.report.get_variant(AblationVariant.A)

print(result.report.summary_table())
print()
print("Faithfulness improvement over baseline (A):")
deltas = result.report.improvement_over_baseline("mean_faithfulness")
for var, d in sorted(deltas.items()):
    sign = "+" if d >= 0 else ""
    print(f"  {var}: {sign}{d:.4f}")

failed = False
if not (vr_f.faithfulness > vr_a.faithfulness):
    print(f"FAIL - REGRESSION: F faithfulness {vr_f.faithfulness:.4f} <= A {vr_a.faithfulness:.4f}")
    failed = True
if not (vr_f.robustness_score > vr_a.robustness_score):
    print("FAIL - REGRESSION: Full arch not more robust than vanilla LLM (A)")
    failed = True

if failed:
    sys.exit(1)

print(f"OK - Dev eval passed ({result.total_cases} cases, {result.n_variants} variants)")
print(f"Report: {result.report_path}")
