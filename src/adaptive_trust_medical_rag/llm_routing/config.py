from __future__ import annotations
import os
from dataclasses import dataclass, field
from pathlib import Path
from adaptive_trust_medical_rag.llm_routing.types import RoutingMode


def load_env_local():
    """Securely parse .env.local without external dependencies, setting os.environ.
    Does NOT print or log secrets."""
    env_file = Path(__file__).parent.parent.parent.parent / ".env.local"
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        k, v = line.split("=", 1)
                        if k not in os.environ:
                            os.environ[k] = v.strip('"\'')

@dataclass
class ProviderConfig:
    """Configuration for a single LLM provider.
    
    api_key_env_var stores the NAME of the environment variable,
    NEVER the actual key value.
    """
    name: str
    priority: int  # 1 = primary, 2 = secondary, etc.
    model_id: str
    api_key_env_var: str

    @property
    def credential_present(self) -> bool:
        val = os.getenv(self.api_key_env_var)
        return bool(val and len(val.strip()) > 0)

    def get_api_key(self) -> str:
        """Retrieve API key from environment. Raises if not set."""
        key = os.getenv(self.api_key_env_var)
        if not key:
            raise RuntimeError(
                f"API key env var {self.api_key_env_var} is not set "
                f"for provider {self.name}"
            )
        return key

    def __repr__(self):
        return f"ProviderConfig(name={self.name}, model_id={self.model_id}, priority={self.priority}, credential_present={self.credential_present})"



@dataclass
class RoutingConfig:
    """Complete routing configuration."""
    providers: list[ProviderConfig] = field(default_factory=list)
    mode: RoutingMode = RoutingMode.APPLICATION
    retry_max_attempts: int = 3
    retry_base_delay: float = 1.0
    retry_max_delay: float = 30.0
    retry_jitter: bool = True
    failover_enabled: bool = True
    circuit_breaker_enabled: bool = True
    circuit_breaker_threshold: int = 5
    circuit_breaker_recovery_seconds: float = 60.0
    secret_redaction: bool = True
    log_raw_keys: bool = False

    def __post_init__(self) -> None:
        # Scientific mode forces failover off
        if self.mode == RoutingMode.SCIENTIFIC:
            self.failover_enabled = False
        
        # Load environment preferences if available
        if os.getenv("LLM_SECRET_REDACTION", "").lower() == "false":
            self.secret_redaction = False
        if os.getenv("LLM_LOG_RAW_KEYS", "").lower() == "true":
            self.log_raw_keys = True

        # Sort providers by priority
        self.providers.sort(key=lambda p: p.priority)

    @staticmethod
    def default_gemini_groq() -> RoutingConfig:
        """Default configuration with Gemini primary, Groq secondary."""
        return RoutingConfig(
            providers=[
                ProviderConfig(
                    name="gemini",
                    priority=1,
                    model_id="gemini-3.1-pro-preview",
                    api_key_env_var="GEMINI_API_KEY",
                ),
                ProviderConfig(
                    name="groq",
                    priority=2,
                    model_id="openai/gpt-oss-120b",
                    api_key_env_var="GROQ_API_KEY",
                ),
            ],
            mode=RoutingMode.APPLICATION,
        )
