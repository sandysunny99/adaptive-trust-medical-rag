"""
Tests for Phase 20 - CI/CD Pipeline Configuration.

Validates the CI workflow YAML structure, all job steps, and the inline
evaluation scripts run correctly in local CI-equivalent mode.
Covers: job structure, evaluation assertions, API health in CI, migration chain.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import yaml

CI_YML = Path(".github/workflows/ci.yml")


def _load_ci() -> dict:
    return yaml.safe_load(CI_YML.read_text(encoding="utf-8"))


class TestCIYamlStructure:
    def test_ci_file_exists(self) -> None:
        assert CI_YML.exists()

    def test_valid_yaml(self) -> None:
        _load_ci()  # raises on invalid YAML

    def test_has_three_jobs(self) -> None:
        ci = _load_ci()
        assert len(ci["jobs"]) == 3

    def test_job_names_correct(self) -> None:
        ci = _load_ci()
        assert "lint-and-test" in ci["jobs"]
        assert "smoke-eval" in ci["jobs"]
        assert "dev-eval" in ci["jobs"]

    def test_smoke_eval_needs_lint(self) -> None:
        ci = _load_ci()
        assert "lint-and-test" in ci["jobs"]["smoke-eval"]["needs"]

    def test_dev_eval_needs_smoke_eval(self) -> None:
        ci = _load_ci()
        assert "smoke-eval" in ci["jobs"]["dev-eval"]["needs"]

    def test_dev_eval_main_only_condition(self) -> None:
        ci = _load_ci()
        condition = ci["jobs"]["dev-eval"].get("if", "")
        assert "main" in condition

    def test_python_version_312(self) -> None:
        ci = _load_ci()
        for job in ci["jobs"].values():
            for step in job["steps"]:
                if step.get("name") == "Set up Python 3.12":
                    assert step["with"]["python-version"] == "3.12"

    def test_uv_version_pinned(self) -> None:
        ci = _load_ci()
        job = ci["jobs"]["lint-and-test"]
        uv_steps = [s for s in job["steps"] if "uv==" in str(s.get("run", ""))]
        assert len(uv_steps) >= 1
        assert "0.12.5" in uv_steps[0]["run"]

    def test_artifact_upload_in_lint_job(self) -> None:
        ci = _load_ci()
        upload_steps = [
            s
            for s in ci["jobs"]["lint-and-test"]["steps"]
            if "upload-artifact" in str(s.get("uses", ""))
        ]
        assert len(upload_steps) >= 1

    def test_smoke_eval_uploads_report(self) -> None:
        ci = _load_ci()
        upload_steps = [
            s
            for s in ci["jobs"]["smoke-eval"]["steps"]
            if "upload-artifact" in str(s.get("uses", ""))
        ]
        assert len(upload_steps) >= 1

    def test_dev_eval_uploads_report_with_sha(self) -> None:
        ci = _load_ci()
        upload_steps = [
            s
            for s in ci["jobs"]["dev-eval"]["steps"]
            if "upload-artifact" in str(s.get("uses", ""))
        ]
        assert len(upload_steps) >= 1
        names = [s["with"]["name"] for s in upload_steps]
        assert any("sha" in n.lower() for n in names)

    def test_gitleaks_step_present(self) -> None:
        ci = _load_ci()
        step_names = [s.get("name", "") for s in ci["jobs"]["lint-and-test"]["steps"]]
        assert any("gitleaks" in n.lower() or "Gitleaks" in n for n in step_names)

    def test_ruff_step_present(self) -> None:
        ci = _load_ci()
        step_names = [s.get("name", "") for s in ci["jobs"]["lint-and-test"]["steps"]]
        assert any("ruff" in n.lower() for n in step_names)

    def test_alembic_verification_step(self) -> None:
        ci = _load_ci()
        steps = ci["jobs"]["lint-and-test"]["steps"]
        assert any("alembic" in s.get("name", "").lower() for s in steps)

    def test_api_health_step(self) -> None:
        ci = _load_ci()
        steps = ci["jobs"]["lint-and-test"]["steps"]
        assert any(
            "api" in s.get("name", "").lower() or "health" in s.get("name", "").lower()
            for s in steps
        )

    def test_hook_tests_present(self) -> None:
        ci = _load_ci()
        steps = ci["jobs"]["lint-and-test"]["steps"]
        hook_steps = [s for s in steps if "hook" in s.get("name", "").lower()]
        assert len(hook_steps) >= 4

    def test_retention_days_smoke(self) -> None:
        ci = _load_ci()
        for step in ci["jobs"]["smoke-eval"]["steps"]:
            if "upload-artifact" in str(step.get("uses", "")):
                assert step["with"]["retention-days"] >= 30

    def test_retention_days_dev_90(self) -> None:
        ci = _load_ci()
        for step in ci["jobs"]["dev-eval"]["steps"]:
            if "upload-artifact" in str(step.get("uses", "")):
                assert step["with"]["retention-days"] >= 90


class TestCIEvalScriptsLocal:
    """Run the inline CI evaluation scripts locally to verify correctness."""

    def test_smoke_eval_script_passes(self) -> None:
        script = """
import os
os.environ["GITHUB_ACTIONS"] = "true"
from pathlib import Path
import tempfile
from adaptive_trust_medical_rag.evaluation.eval_pipeline import run_evaluation
from adaptive_trust_medical_rag.evaluation.evaluator import DatasetSplit
from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
    AblationVariant, ExperimentTracker
)
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    result = run_evaluation(
        split=DatasetSplit.smoke,
        variants=[AblationVariant.B, AblationVariant.F],
        tracker=ExperimentTracker(experiment_name="ci-test", log_dir=tmp / "logs"),
        reports_dir=tmp / "reports",
        logs_dir=tmp / "logs",
        bootstrap=False,
        experiment_name="ci-test",
    )
    vr_f = result.report.get_variant(AblationVariant.F)
    vr_b = result.report.get_variant(AblationVariant.B)
    assert vr_f.faithfulness > vr_b.faithfulness
    print("PASS")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            env={
                **__import__("os").environ,
                "PYTHONPATH": "src",
                "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
            },
        )
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"
        assert "PASS" in result.stdout

    def test_api_health_script_passes(self) -> None:
        script = """
from fastapi.testclient import TestClient
from adaptive_trust_medical_rag.api.app import create_app
app = create_app()
client = TestClient(app)
resp = client.get("/health")
assert resp.status_code == 200
data = resp.json()
assert "status" in data
assert "version" in data
print("PASS")
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            env={
                **__import__("os").environ,
                "PYTHONPATH": "src",
                "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
            },
        )
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"
        assert "PASS" in result.stdout

    def test_migration_chain_script_passes(self) -> None:
        script = """
from adaptive_trust_medical_rag.database.migration_utils import (
    verify_migration_chain, get_migration_chain
)
errors = verify_migration_chain()
assert errors == [], f"Chain errors: {errors}"
chain = get_migration_chain()
assert len(chain) >= 1
print("PASS chain:", chain)
"""
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            env={
                **__import__("os").environ,
                "PYTHONPATH": "src",
                "DATABASE_URL": "postgresql+asyncpg://u:p@localhost/db",
            },
        )
        assert result.returncode == 0, f"Script failed:\n{result.stderr}"
        assert "PASS" in result.stdout

    def test_smoke_eval_faithfulness_regression_guard(self) -> None:
        """F must beat B on faithfulness — core regression check."""
        import tempfile
        from pathlib import Path

        from adaptive_trust_medical_rag.evaluation.eval_pipeline import run_evaluation
        from adaptive_trust_medical_rag.evaluation.evaluator import DatasetSplit
        from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
            AblationVariant,
            ExperimentTracker,
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = run_evaluation(
                split=DatasetSplit.smoke,
                variants=[AblationVariant.B, AblationVariant.F],
                tracker=ExperimentTracker(experiment_name="test", log_dir=tmp_path / "logs"),
                reports_dir=tmp_path / "reports",
                logs_dir=tmp_path / "logs",
                bootstrap=False,
            )
            vr_f = result.report.get_variant(AblationVariant.F)
            vr_b = result.report.get_variant(AblationVariant.B)
            assert vr_f is not None
            assert vr_b is not None
            assert vr_f.faithfulness > vr_b.faithfulness

    def test_markdown_report_saved_to_disk(self) -> None:
        import tempfile
        from pathlib import Path

        from adaptive_trust_medical_rag.evaluation.eval_pipeline import run_evaluation
        from adaptive_trust_medical_rag.evaluation.evaluator import DatasetSplit
        from adaptive_trust_medical_rag.evaluation.experiment_tracker import (
            AblationVariant,
            ExperimentTracker,
        )

        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            result = run_evaluation(
                split=DatasetSplit.smoke,
                variants=[AblationVariant.F],
                tracker=ExperimentTracker(experiment_name="test", log_dir=tmp_path / "logs"),
                reports_dir=tmp_path / "reports",
                logs_dir=tmp_path / "logs",
                bootstrap=False,
            )
            assert result.report_path.exists()
            content = result.report_path.read_text()
            assert "Ablation Study Report" in content
            assert "Research Integrity" in content
