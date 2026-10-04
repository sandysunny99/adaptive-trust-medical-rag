from typing import Dict, Any
import hashlib

class ExperimentRunner:
    def __init__(self, config):
        self.config = config
        self._validate_contract()

    def _validate_contract(self):
        if getattr(self.config, "execution_authorized", False) is not True:
            raise RuntimeError("Execution is NOT AUTHORIZED by researcher.")
        if getattr(self.config, "retry_max_attempts", 0) != 0:
            raise RuntimeError("V1.1 protocol violation: retries enabled")
        if getattr(self.config, "fallback_enabled", False) is not False:
            raise RuntimeError("V1.1 protocol violation: fallback enabled")
        if getattr(self.config, "failover_enabled", False) is not False:
            raise RuntimeError("V1.1 protocol violation: failover enabled")
        if getattr(self.config, "imputation_enabled", False) is not False:
            raise RuntimeError("V1.1 protocol violation: imputation enabled")

    def generate_snapshot(self, arm: str) -> Dict[str, Any]:
        return {
            "provider": self.config.provider,
            "model": self.config.model,
            "temperature": self.config.temperature,
            "retry_max_attempts": self.config.retry_max_attempts,
            "fallback_enabled": self.config.fallback_enabled,
            "failover_enabled": self.config.failover_enabled,
            "imputation_enabled": self.config.imputation_enabled,
            "prompt_version": self.config.prompt_version,
            "prompt_template_hash": self.config.prompt_hash,
            "dataset_hash": self.config.dataset_hash,
            "arm": arm,
            "adaptive_control_enabled": arm == "ARM_B_ADAPTIVE"
        }

    def instantiate_prompt(self, query: str, evidence: list, risk_tier: str) -> str:
        # Strictly deterministic prompt representation
        evidence_text = "\n".join(f"[{e.get('chunk_id','')}] {e.get('text','')}" for e in evidence)
        return f"SYSTEM: Answer {query} carefully.\nEVIDENCE:\n{evidence_text}\nRISK: {risk_tier}"

    def execute_case(self, case_id: str, query: str, evidence: list, risk_tier: str, arm: str, backend_mock) -> Dict[str, Any]:
        if not getattr(self.config, "execution_authorized", False):
            raise RuntimeError("Execution is NOT AUTHORIZED by researcher.")
        
        instantiated_prompt = self.instantiate_prompt(query, evidence, risk_tier)
        prompt_hash = hashlib.sha256(instantiated_prompt.encode('utf-8')).hexdigest()
        
        try:
            response = backend_mock.generate(query=query, evidence=evidence, arm=arm, final_prompt=instantiated_prompt)
            return {"status": "SUCCESS", "response": response, "attempts": 1, "instantiated_prompt_hash": prompt_hash, "instantiated_prompt": instantiated_prompt}
        except Exception as e:
            return {"status": "PROVIDER_FAILURE", "error": str(e), "attempts": 1, "instantiated_prompt_hash": prompt_hash, "instantiated_prompt": instantiated_prompt}
