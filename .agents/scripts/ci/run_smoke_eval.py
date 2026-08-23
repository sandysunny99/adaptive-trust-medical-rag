#!/usr/bin/env python
"""CI: Run smoke ablation evaluation (Variants B + F) and assert F > B faithfulness."""

import sys
from pathlib import Path

sys.path.insert(0, "src")

from adaptive_trust_medical_rag.evaluation.eval_pipeline import run_evaluation
from adaptive_trust_medical_rag.evaluation.evaluator import DatasetSplit
from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
    AblationVariant,
    ExperimentTracker,
)

reports_dir = Path("ci-reports/smoke")
logs_dir = Path("ci-reports/logs")
reports_dir.mkdir(parents=True, exist_ok=True)
logs_dir.mkdir(parents=True, exist_ok=True)

result = run_evaluation(
    split=DatasetSplit.smoke,
    variants=[AblationVariant.B, AblationVariant.F],
    tracker=ExperimentTracker(experiment_name="ci-smoke", log_dir=logs_dir),
    reports_dir=reports_dir,
    logs_dir=logs_dir,
    bootstrap=False,
    experiment_name="ci-smoke-ablation",
)

vr_f = result.report.get_variant(AblationVariant.F)
vr_b = result.report.get_variant(AblationVariant.B)

print(result.report.summary_table())
print(f"Variant F faithfulness: {vr_f.faithfulness:.4f}")
print(f"Variant B faithfulness: {vr_b.faithfulness:.4f}")

if not (vr_f.faithfulness > vr_b.faithfulness):
    print(f"FAIL - REGRESSION: F={vr_f.faithfulness:.4f} <= B={vr_b.faithfulness:.4f}")
    sys.exit(1)

print(f"OK - Smoke eval passed. Report: {result.report_path}")
