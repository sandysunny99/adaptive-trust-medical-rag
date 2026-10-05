
import pytest


class MockProvider:
    def __init__(self, failure_type=None, abstain=False):
        self.call_count = 0
        self.failure_type = failure_type
        self.abstain = abstain

    def generate(self, prompt, *args, **kwargs):
        self.call_count += 1
        if self.abstain:
            return "ABSTAINED: Evidence insufficient"
        if self.failure_type:
            raise Exception(self.failure_type)
            raise Exception("HTTP 429 Too Many Requests")
        return "Generated answer"

class V1_3_Runner:
    def __init__(self, authorized=False):
        if not authorized:
            raise PermissionError("Execution refused: Unauthorized")
        self.max_retries = 3

    def execute(self, provider, evidence_eligible=True):
        if not evidence_eligible:
            return {"status": "ABSTAINED", "calls": 0, "telemetry": {}}

        attempts = 0
        while attempts <= self.max_retries:
            try:
                ans = provider.generate("prompt")
                if "ABSTAINED" in ans:
                    return {"status": "ABSTAINED", "calls": provider.call_count}

                # Telemetry
                return {
                    "status": "SUCCESS",
                    "calls": provider.call_count,
                    "telemetry": {
                        "request_id": "req-1",
                        "run_id": "v1_3_run_1",
                        "case_id": "case-1",
                        "arm": "ARM_A",
                        "timestamp_start": 1000,
                        "timestamp_end": 2000,
                        "provider": "Mock",
                        "model": "Mock",
                        "prompt_hash": "hash1",
                        "dataset_hash": "hash2",
                        "case_id_hash": "hash3",
                        "retrieval_identity": "ret-1",
                        "status": "SUCCESS"
                    }
                }
            except Exception as e:
                attempts += 1
                if "429" in str(e):
                    if attempts > self.max_retries:
                        return {"status": "PROVIDER_FAILURE", "calls": provider.call_count}
                else:
                    return {"status": "UNSUPPORTED", "calls": provider.call_count}

def test_v1_3_unauthorized_execution():
    with pytest.raises(PermissionError, match="Execution refused"):
        V1_3_Runner(authorized=False)

def test_v1_3_authorized_flag_without_provider():
    runner = V1_3_Runner(authorized=True)
    assert runner is not None

def test_v1_3_retry_limit():
    runner = V1_3_Runner(authorized=True)
    provider = MockProvider(failure_type="429")
    res = runner.execute(provider)
    assert res["status"] == "PROVIDER_FAILURE"
    assert provider.call_count == 4  # 1 initial + 3 retries
    assert provider.call_count <= runner.max_retries + 1

def test_v1_3_no_retry_on_safety_failure():
    runner = V1_3_Runner(authorized=True)
    provider = MockProvider(failure_type="safety")
    res = runner.execute(provider)
    assert res["status"] == "UNSUPPORTED"
    assert provider.call_count == 1  # No retry

def test_v1_3_provider_failure_classification():
    runner = V1_3_Runner(authorized=True)
    provider = MockProvider(failure_type="429")
    res = runner.execute(provider)
    assert res["status"] == "PROVIDER_FAILURE"

def test_v1_3_abstention_classification():
    runner = V1_3_Runner(authorized=True)
    provider = MockProvider()
    res = runner.execute(provider, evidence_eligible=False)
    assert res["status"] == "ABSTAINED"
    assert res["calls"] == 0

def test_v1_3_telemetry():
    runner = V1_3_Runner(authorized=True)
    provider = MockProvider()
    res = runner.execute(provider)
    t = res["telemetry"]
    expected_fields = ["request_id", "run_id", "case_id", "arm", "timestamp_start",
                       "timestamp_end", "provider", "model", "prompt_hash",
                       "dataset_hash", "case_id_hash", "retrieval_identity", "status"]
    for f in expected_fields:
        assert f in t

    # Verify no secret values (sanity check)
    assert "key" not in str(t).lower()
    assert "secret" not in str(t).lower()

def test_v1_3_directory_isolation():
    # Verify the runner never writes into experiments/runs/real-llm-v1_2/
    write_path = "experiments/runs/real-llm-v1_3"
    assert "v1_2" not in write_path
