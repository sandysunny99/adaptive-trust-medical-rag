import json
import os
from pathlib import Path
import pytest
from adaptive_trust_medical_rag.evaluation.phase15_runner import Phase15Runner, PreflightError, ExecutionError, FROZEN_DATASET_HASH

@pytest.fixture
def temp_dataset(tmp_path):
    dataset_path = tmp_path / "phase15_cases.jsonl"
    cases = [{"case_id": f"C{str(i).zfill(3)}"} for i in range(200)]
    with open(dataset_path, "w") as f:
        for case in cases:
            f.write(json.dumps(case) + "\n")
    return dataset_path

@pytest.fixture
def mock_runner(temp_dataset, tmp_path):
    output_dir = tmp_path / "runs"
    runner = Phase15Runner(temp_dataset, output_dir)
    return runner

def test_missing_dataset(tmp_path):
    runner = Phase15Runner(tmp_path / "nonexistent.jsonl", tmp_path / "runs")
    with pytest.raises(PreflightError, match="Dataset not found"):
        runner.preflight_check()

def test_hash_mismatch(mock_runner):
    with pytest.raises(PreflightError, match="Dataset hash mismatch"):
        mock_runner.preflight_check()

def test_wrong_case_count(mock_runner, temp_dataset):
    # Fix hash check for this specific test by mocking the _compute_file_hash
    mock_runner._compute_file_hash = lambda x: FROZEN_DATASET_HASH
    
    # Append an extra line to mess up the count
    with open(temp_dataset, "a") as f:
        f.write('{"case_id": "C201"}\n')
        
    with pytest.raises(PreflightError, match="Case count mismatch"):
        mock_runner.preflight_check()

def test_duplicate_cases(mock_runner, temp_dataset):
    mock_runner._compute_file_hash = lambda x: FROZEN_DATASET_HASH
    
    # Write exactly 200 cases, but make two of them have the same ID
    cases = [{"case_id": f"C{str(i).zfill(3)}"} for i in range(199)]
    cases.append({"case_id": "C000"}) # Duplicate
    with open(temp_dataset, "w") as f:
        for case in cases:
            f.write(json.dumps(case) + "\n")
            
    with pytest.raises(PreflightError, match="Duplicate case_id found: C000"):
        mock_runner.preflight_check()

def test_successful_preflight(mock_runner):
    mock_runner._compute_file_hash = lambda x: FROZEN_DATASET_HASH
    manifest = mock_runner.preflight_check()
    assert manifest["expected_cases"] == 200
    assert manifest["execution_mode"] == "PREFLIGHT"
    assert manifest["status"] == "PREFLIGHT_PASS"
    assert (mock_runner.run_dir / "run_manifest.json").exists()

def test_execute_without_flag_halts(mock_runner):
    mock_runner._compute_file_hash = lambda x: FROZEN_DATASET_HASH
    mock_runner.preflight_check()
    # Should return safely without executing anything
    mock_runner.execute(require_execute_flag=True, execute_flag_passed=False)

def test_execute_missing_credentials(mock_runner, monkeypatch):
    mock_runner._compute_file_hash = lambda x: FROZEN_DATASET_HASH
    mock_runner.preflight_check()
    
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    
    with pytest.raises(ExecutionError, match="Missing GEMINI_API_KEY"):
        mock_runner.execute(require_execute_flag=True, execute_flag_passed=True)
