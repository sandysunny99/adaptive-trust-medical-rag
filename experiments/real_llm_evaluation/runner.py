from typing import Dict, Any

class ExperimentRunner:
    def __init__(self, config):
        self.config = config
        assert self.config.retry_max_attempts == 0, "Protocol requires NO RETRIES"
        assert self.config.failover_enabled == False, "Protocol requires NO FALLBACK"

    def generate_snapshot(self, arm: str) -> Dict[str, Any]:
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "retry_max_attempts": self.config.retry_max_attempts,
            "failover_enabled": self.config.failover_enabled,
            "prompt_version": self.config.prompt_version,
            "prompt_hash": self.config.prompt_hash,
            "dataset_hash": self.config.dataset_hash,
            "arm": arm,
            "adaptive_control_enabled": arm == "ARM_B_ADAPTIVE"
        }

    def execute_case(self, case_id: str, arm: str, backend_mock) -> Dict[str, Any]:
        # Enforce exact 1 attempt
        try:
            response = backend_mock.generate()
            return {"status": "SUCCESS", "response": response, "attempts": 1}
        except Exception as e:
            return {"status": "PROVIDER_FAILURE", "error": str(e), "attempts": 1}
