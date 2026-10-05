import pytest

from experiments.real_llm_evaluation.runner import ExperimentRunner


class MockConfig:
    provider = "Groq"
    model = "openai/gpt-oss-120b"
    temperature = 0
    retry_max_attempts = 0
    fallback_enabled = False
    failover_enabled = False
    imputation_enabled = False
    prompt_version = "v1.2"
    prompt_hash = "mock_hash"
    dataset_hash = "mock_hash"
    execution_authorized = False  # UNAUTHORIZED

class MockBackend:
    def __init__(self):
        self.call_count = 0
    def generate(self, *args, **kwargs):
        self.call_count += 1
        return "Mock response"

def test_runner_unauthorized_blocks_execution():
    config = MockConfig()

    # Initialization should raise an error immediately because it's unauthorized
    with pytest.raises(RuntimeError, match="NOT AUTHORIZED"):
        runner = ExperimentRunner(config)

    # Even if initialized somehow, execute_case should block
    config.execution_authorized = True
    runner = ExperimentRunner(config)
    config.execution_authorized = False

    backend = MockBackend()

    with pytest.raises(RuntimeError, match="NOT AUTHORIZED"):
        runner.execute_case(
            case_id="case1",
            query="test",
            evidence=[],
            risk_tier="R1",
            arm="ARM_A",
            backend_mock=backend
        )

    assert backend.call_count == 0
