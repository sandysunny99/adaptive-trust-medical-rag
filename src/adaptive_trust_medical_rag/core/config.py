"""Application configuration — Pydantic Settings."""

from __future__ import annotations

from enum import Enum

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppEnv(str, Enum):
    development = "development"
    staging = "staging"
    production = "production"


class TrustThresholds(BaseSettings):
    """Risk-class trust score thresholds from AGENTS.md."""

    model_config = SettingsConfigDict(env_prefix="TRUST_THRESHOLD_")

    r0: float = Field(0.30, ge=0.0, le=1.0, description="R0 Informational threshold")
    r1: float = Field(0.45, ge=0.0, le=1.0, description="R1 Low-risk threshold")
    r2: float = Field(0.60, ge=0.0, le=1.0, description="R2 Medium-risk threshold")
    r3: float = Field(0.75, ge=0.0, le=1.0, description="R3 High-risk threshold")

    def for_risk_class(self, risk_class: int) -> float:
        """Return the threshold for the given risk class (0–3)."""
        mapping = {0: self.r0, 1: self.r1, 2: self.r2, 3: self.r3}
        if risk_class not in mapping:
            raise ValueError(f"Invalid risk class: {risk_class}. Must be 0–3.")
        return mapping[risk_class]


class Settings(BaseSettings):
    """Central application settings loaded from environment variables / .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ──────────────────────────────────────────────────────────
    app_env: AppEnv = AppEnv.development
    log_level: str = "INFO"

    # ── Database ─────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://rag_user:changeme@localhost:5432/medical_rag",
        description="Async PostgreSQL connection URL",
    )
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "medical_rag"
    postgres_user: str = "rag_user"

    # ── Trust Thresholds ─────────────────────────────────────────────────────
    trust_threshold_r0: float = Field(0.30, ge=0.0, le=1.0)
    trust_threshold_r1: float = Field(0.45, ge=0.0, le=1.0)
    trust_threshold_r2: float = Field(0.60, ge=0.0, le=1.0)
    trust_threshold_r3: float = Field(0.75, ge=0.0, le=1.0)

    @field_validator("database_url")
    @classmethod
    def validate_no_plaintext_credentials_in_code(cls, v: str) -> str:
        """Warn if URL contains placeholder passwords."""
        if "changeme" in v or "REPLACE" in v:
            import warnings

            warnings.warn(
                "DATABASE_URL contains placeholder credentials. "
                "Set a real password in your .env file.",
                stacklevel=2,
            )
        return v

    def trust_threshold(self, risk_class: int) -> float:
        """Return trust threshold for a given risk class (0–3)."""
        mapping = {
            0: self.trust_threshold_r0,
            1: self.trust_threshold_r1,
            2: self.trust_threshold_r2,
            3: self.trust_threshold_r3,
        }
        if risk_class not in mapping:
            raise ValueError(f"Invalid risk class: {risk_class}. Must be 0–3.")
        return mapping[risk_class]


# Module-level singleton — import and use across the application
settings = Settings()
