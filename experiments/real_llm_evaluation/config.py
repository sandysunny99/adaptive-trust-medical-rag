from dataclasses import dataclass
from typing import Optional

@dataclass
class RealLLMEvaluationConfig:
    provider: str = "Groq"
    model: str = "openai/gpt-oss-120b"
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    seed_support: str = "NOT_SUPPORTED"
    retry_max_attempts: int = 0
    failover_enabled: bool = False
    prompt_version: str = "REAL_LLM_PROMPT_V1"
    prompt_hash: str = "1d461a83fd6ade33291ce565a0032cdb01c73d2b76386dc68c5dc12aa0970c09"
    dataset_manifest: str = "experiments/manifests/v3_1_human_cases.json"
    dataset_hash: str = "db4013a97bed7d05803abe73cfeb477a3a82e6c75c30f860d76eed655add59dc"
    retrieval_snapshot: str = "FROZEN_HISTORICAL_OUTPUT"
    request_budget: int = 160
