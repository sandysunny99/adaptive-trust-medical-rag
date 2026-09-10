
import pytest

from adaptive_trust_medical_rag.evaluation.experiment_tracker import ExperimentConfig
from adaptive_trust_medical_rag.research_harness.approval_manager import (
    ApprovalManager,
    ApprovalState,
)
from adaptive_trust_medical_rag.research_harness.artifact_registry import ArtifactRegistry
from adaptive_trust_medical_rag.research_harness.failure_taxonomy import (
    FailureCategory,
    FailureIssue,
    Severity,
)
from adaptive_trust_medical_rag.research_harness.gate_engine import GateEngine, GateStatus
from adaptive_trust_medical_rag.research_harness.run_manifest import RunManifest


def test_failure_taxonomy_serialization():
    issue = FailureIssue(
        issue_id="ISSUE-001",
        category=FailureCategory.BLOCKING_ANNOTATION,
        severity=Severity.HIGH,
        description="Missing human_final_label column",
        blocking=True
    )
    d = issue.to_dict()
    assert d["category"] == "BLOCKING_ANNOTATION"
    assert d["severity"] == "HIGH"
    assert d["blocking"] is True

    issue2 = FailureIssue.from_dict(d)
    assert issue2.category == FailureCategory.BLOCKING_ANNOTATION
    assert issue2.issue_id == "ISSUE-001"


def test_artifact_registry(tmp_path):
    registry_file = tmp_path / "registry.json"
    registry = ArtifactRegistry(registry_file)

    test_file = tmp_path / "test_artifact.txt"
    test_file.write_text("Hello World", encoding="utf-8")

    # 1. Register artifact
    meta = registry.register(
        artifact_id="artifact_1",
        file_path=test_file,
        experiment_id="exp1",
        role="test",
        frozen=True
    )
    assert meta.artifact_id == "artifact_1"
    assert registry.verify("artifact_1") is True

    # 2. Duplicate frozen registration fails
    with pytest.raises(ValueError, match="is frozen"):
        registry.register("artifact_1", test_file, "exp1", "test")

    # 3. Changed artifact detection (fails closed)
    test_file.write_text("Modified Content", encoding="utf-8")
    assert registry.verify("artifact_1") is False

    # 4. Missing artifact detection (fails closed)
    test_file.unlink()
    assert registry.verify("artifact_1") is False


def test_run_manifest():
    manifest = RunManifest(
        experiment_id="exp-1",
        run_id="run-1",
        timestamp="2026-09-05T00:00:00Z",
        code_version="v1",
        configuration={"key": "val"},
        inputs={"in": 1},
        artifacts=["art1"],
        artifact_hashes={"art1": "hash"},
        environment={"OS": "linux"},
        outputs={"out": 2},
        metrics={"acc": 0.9},
        gate_results={"gate1": "PASS"},
        approval_state="APPROVED",
        status="SUCCESS",
        notes="None"
    )

    j = manifest.to_json()
    assert "exp-1" in j

    manifest2 = RunManifest.from_json(j)
    assert manifest2.experiment_id == "exp-1"
    assert manifest2.approval_state == "APPROVED"
    assert manifest2.inputs["in"] == 1


def test_gate_engine():
    engine = GateEngine()

    # Passing gate
    engine.register_gate("G1", "Gate 1", False, lambda: {"passed": True, "evidence": {"val": 1}})
    # Blocking failure gate
    engine.register_gate("G2", "Gate 2", True, lambda: {"passed": False, "evidence": {"val": 2}})
    # Gate that should be skipped
    engine.register_gate("G3", "Gate 3", False, lambda: {"passed": True, "evidence": {}})

    report = engine.evaluate()

    assert report.overall_status == GateStatus.FAIL
    assert report.failed_gate_id == "G2"
    assert len(report.results) == 3

    assert report.results[0].status == GateStatus.PASS
    assert report.results[1].status == GateStatus.FAIL
    assert report.results[2].status == GateStatus.SKIPPED


def test_approval_manager():
    manager = ApprovalManager()

    # 1. Request
    record = manager.request_approval("exp1", "run1")
    assert record.state == ApprovalState.PENDING

    # 2. Approve
    approved = manager.approve("exp1", "run1", "ReviewerA", "Looks good")
    assert approved.state == ApprovalState.APPROVED
    assert approved.approver == "ReviewerA"

    # 3. Invalid transition (reject after approve)
    with pytest.raises(ValueError):
        manager.reject("exp1", "run1", "ReviewerB", "Wait")

    # 4. Revoke
    revoked = manager.revoke("exp1", "run1", "Admin", "Found error")
    assert revoked.state == ApprovalState.REVOKED


def test_experiment_tracker_integration():
    # Verify backward compatibility and new fields
    config = ExperimentConfig(
        model_name="test-model",
        model_temperature=0.0,
        trust_weights={"authority": 0.5},
        dataset_name="test-ds",
        dataset_version="v1",
        dataset_split="test",
        ablation_variant="F"
    )

    # Ensure our injected fields exist
    assert hasattr(config, "gate_results")
    assert hasattr(config, "approval_state")
    assert config.approval_state == "PENDING"

    params = config.to_mlflow_params()
    assert "approval_state" in params
    assert params["approval_state"] == "PENDING"
