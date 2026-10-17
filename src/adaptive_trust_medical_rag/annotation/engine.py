"""AI-Assisted Annotation Engine for Track A Medical Evidence Relevance Evaluation.

Executes positions through frozen adjudication prompts with strict 21-field
structured output verification, span grounding checks, and prompt hash auditing.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Callable, Coroutine, Optional

from adaptive_trust_medical_rag.annotation.schemas import (
    AIRecommendation,
    AnnotationPosition,
    AnnotationSessionConfig,
)

logger = logging.getLogger(__name__)


class PromptHashMismatchError(ValueError):
    """Raised when on-disk prompts do not match frozen cryptographic hashes."""

    pass


class AIAnnotationEngine:
    """Processes retrieval positions through the LLM adjudication pipeline."""

    def __init__(
        self,
        config: AnnotationSessionConfig,
        llm_backend: Optional[Any] = None,
        workspace_dir: Optional[Path | str] = None,
    ) -> None:
        """Initialize the AI Annotation Engine.

        Args:
            config: Annotation session configuration.
            llm_backend: Optional pre-configured LLM backend/adapter (for mocking/testing or custom routing).
            workspace_dir: Base directory containing prompts and schema files.
        """
        self.config = config
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()

        # Locate prompt and schema paths
        self.system_prompt_path = self._resolve_path(
            config.system_prompt_path,
            "track_a_annotation/decision_batches/TRACK_A_LLM_SYSTEM_PROMPT_V2.txt",
        )
        self.adjudication_prompt_path = self._resolve_path(
            config.adjudication_prompt_path,
            "track_a_annotation/decision_batches/TRACK_A_LLM_ADJUDICATION_PROMPT_V2.txt",
        )
        self.challenge_prompt_path = self._resolve_path(
            config.challenge_prompt_path,
            "track_a_annotation/decision_batches/TRACK_A_LLM_CHALLENGE_PROMPT_V2.txt",
        )
        self.schema_path = self._resolve_path(
            config.schema_path,
            "track_a_annotation/decision_batches/TRACK_A_ADJUDICATION_SCHEMA_FINAL_V1.json",
        )
        self.frozen_hashes_path = self._resolve_path(
            None,
            "track_a_annotation/decision_batches/TRACK_A_LLM_FINAL_SCHEMA_HASHES_V1.json",
        )

        # Load prompts and schemas
        self.system_prompt = self._load_text(self.system_prompt_path)
        self.adjudication_prompt_template = self._load_text(self.adjudication_prompt_path)
        self.challenge_prompt = self._load_text(self.challenge_prompt_path)
        self.schema_dict = self._load_json(self.schema_path)

        # Compute prompt and schema hashes
        self.prompt_hashes = self._compute_hashes()

        # Verify prompt hashes if configured
        if self.config.verify_prompt_hashes:
            self._verify_hashes()

        # Initialize LLM backend adapter
        self.llm_backend = llm_backend or self._initialize_backend()

    def _resolve_path(self, configured_path: Optional[str | Path], default_rel_path: str) -> Path:
        """Resolve a path relative to workspace directory."""
        if configured_path:
            p = Path(configured_path)
            return p if p.is_absolute() else (self.workspace_dir / p).resolve()
        return (self.workspace_dir / default_rel_path).resolve()

    def _load_text(self, path: Path) -> str:
        """Load text file with utf-8 encoding."""
        if not path.exists():
            raise FileNotFoundError(f"Required prompt file not found: {path}")
        with open(path, encoding="utf-8") as f:
            return f.read()

    def _load_json(self, path: Path) -> dict[str, Any]:
        """Load JSON file with utf-8 encoding."""
        if not path.exists():
            raise FileNotFoundError(f"Required JSON file not found: {path}")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _compute_hashes(self) -> dict[str, str]:
        """Compute SHA256 hashes for system, adjudication, challenge prompts, and schema.

        Prompts are hashed as the raw file bytes, as the frozen hashes were recorded
        (track_a_annotation/decision_batches/gen_final_v14.py reads them with "rb"). Text mode
        would turn CRLF into LF and hash different bytes. The schema hash is its canonical JSON.
        """
        canon_schema = json.dumps(self.schema_dict, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
        return {
            "system_prompt_sha256": hashlib.sha256(self.system_prompt_path.read_bytes()).hexdigest(),
            "adjudication_prompt_sha256": hashlib.sha256(
                self.adjudication_prompt_path.read_bytes()
            ).hexdigest(),
            "challenge_prompt_sha256": hashlib.sha256(
                self.challenge_prompt_path.read_bytes()
            ).hexdigest(),
            "track_a_adjudication_schema_sha256": hashlib.sha256(canon_schema).hexdigest(),
        }

    def _verify_hashes(self) -> None:
        """Verify prompt hashes against the frozen hash specification."""
        if not self.frozen_hashes_path.exists():
            logger.warning(f"Frozen prompt hash manifest not found at: {self.frozen_hashes_path}")
            return

        frozen = self._load_json(self.frozen_hashes_path)
        for key, expected_hash in frozen.items():
            if key in self.prompt_hashes:
                actual_hash = self.prompt_hashes[key]
                if actual_hash != expected_hash:
                    raise PromptHashMismatchError(
                        f"Cryptographic hash mismatch for '{key}': expected {expected_hash}, got {actual_hash}. "
                        "Prompt or schema may have been modified from frozen baseline."
                    )

    def _initialize_backend(self) -> Any:
        """Initialize provider adapter using existing llm_backend infrastructure."""
        provider = self.config.provider.lower()

        if provider == "mock":
            from adaptive_trust_medical_rag.llm_backend.mock_backend import MockLLMBackend

            return MockLLMBackend()

        if provider == "groq":
            try:
                from adaptive_trust_medical_rag.llm_backend.pilot_adapter import LLMProviderAdapter

                return LLMProviderAdapter(
                    execution_mode="DIRECT_GROQ",
                    model=self.config.model,
                    structured_output_method=self.config.structured_output_method,
                )
            except Exception as e:
                logger.info(f"Pilot adapter fallback for Groq: {e}")
                from adaptive_trust_medical_rag.llm_backend.groq_backend import GroqBackend
                import os

                return GroqBackend(
                    api_key=os.getenv("GROQ_API_KEY", ""),
                    model_name=self.config.model,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                )

        if provider == "nvidia":
            import os
            from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import (
                OpenAICompatibleBackend,
            )

            api_key = os.getenv("NVIDIA_API_KEY") or os.getenv("NVIDIA_LLM_API_KEY", "")
            return OpenAICompatibleBackend(
                provider_name="nvidia",
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=api_key,
                model_name=self.config.model,
                max_tokens=self.config.max_tokens,
            )

        if provider in ("gemini", "google"):
            import os
            from adaptive_trust_medical_rag.llm_backend.google_gemini_backend import (
                GoogleGeminiBackend,
            )

            return GoogleGeminiBackend(
                api_key=os.getenv("GEMINI_API_KEY", ""),
                model_name=self.config.model,
            )

        if provider == "cloudflare":
            from adaptive_trust_medical_rag.llm_backend.pilot_adapter import LLMProviderAdapter

            return LLMProviderAdapter(
                execution_mode="DIRECT_CLOUDFLARE",
                model=self.config.model,
                structured_output_method=self.config.structured_output_method,
            )

        # Fallback to general LLMProviderAdapter or generic interface
        try:
            from adaptive_trust_medical_rag.llm_backend.pilot_adapter import LLMProviderAdapter

            mode_map = {
                "huggingface": "DIRECT_HUGGINGFACE",
                "freellmapi": "FREELLMAPI_GATEWAY",
            }
            if provider in mode_map:
                return LLMProviderAdapter(
                    execution_mode=mode_map[provider],
                    model=self.config.model,
                    structured_output_method=self.config.structured_output_method,
                )
        except Exception as exc:
            # Only the provider and the exception type: a message can carry a key or a URL.
            # Returning None keeps the safe failure in annotate_position.
            logger.warning(
                "LLM adapter initialization failed for provider %s (%s); no backend configured",
                provider, type(exc).__name__,
            )

        return None

    def format_prompt(self, query: str, evidence: str) -> str:
        """Format adjudication prompt template with query and retrieved evidence."""
        return self.adjudication_prompt_template.format(query=query, evidence=evidence)

    def _get_response_format(self) -> dict[str, Any]:
        """Construct response format specification for structured generation."""
        if self.config.structured_output_method == "NATIVE_JSON_SCHEMA":
            return {
                "type": "json_schema",
                "json_schema": {
                    "name": "semantic_adjudication",
                    "strict": True,
                    "schema": self.schema_dict,
                },
            }
        return {"type": "json_object"}

    async def annotate_position(self, position: AnnotationPosition) -> AIRecommendation:
        """Send a single position through the LLM for annotation recommendation.

        Note: Never auto-commits to human annotator files.

        Args:
            position: The retrieval position to evaluate.

        Returns:
            Validated AIRecommendation instance.
        """
        user_prompt = self.format_prompt(
            query=position.query_text,
            evidence=position.retrieved_evidence,
        )
        response_format = self._get_response_format()

        raw_output: Any = None

        if self.llm_backend is None:
            raise RuntimeError(
                f"LLM backend for provider '{self.config.provider}' is not configured or missing credentials."
            )

        # 1. Custom callable (useful for unit tests and mocks)
        if callable(self.llm_backend) and not hasattr(self.llm_backend, "generate_structured"):
            if asyncio.iscoroutinefunction(self.llm_backend):
                raw_output = await self.llm_backend(
                    self.system_prompt, user_prompt, self.schema_dict
                )
            else:
                raw_output = self.llm_backend(self.system_prompt, user_prompt, self.schema_dict)

        # 2. LLMProviderAdapter (from pilot_adapter.py)
        elif hasattr(self.llm_backend, "generate_structured") and hasattr(
            self.llm_backend, "structured_output_method"
        ):
            gen_cfg = {
                "evidence_text": position.retrieved_evidence,
                "temperature": self.config.temperature,
                "top_p": self.config.top_p,
                "max_tokens": self.config.max_tokens,
                "seed": self.config.seed,
                "timeout": self.config.timeout_seconds,
            }
            # pilot_adapter.generate_structured is synchronous
            res = self.llm_backend.generate_structured(
                system_prompt=self.system_prompt,
                user_prompt=user_prompt,
                schema=self.schema_dict,
                generation_config=gen_cfg,
            )
            if not res.get("success"):
                raise RuntimeError(
                    f"LLMProviderAdapter execution failed: {res.get('error_type')}: {res.get('error_message')}"
                )
            raw_output = res.get("parsed_output")

        # 3. ProviderAdapter / Async generate_structured
        elif hasattr(self.llm_backend, "generate_structured"):
            # Asynchronous provider adapter (OpenAICompatibleBackend, Router, etc.)
            full_prompt = f"{self.system_prompt}\n\n{user_prompt}"
            resp = await self.llm_backend.generate_structured(full_prompt, response_format)
            raw_output = getattr(resp, "structured_output", None) or getattr(resp, "content", None)

        # 4. Standard generate(prompt)
        elif hasattr(self.llm_backend, "generate"):
            full_prompt = f"{self.system_prompt}\n\n{user_prompt}"
            if asyncio.iscoroutinefunction(self.llm_backend.generate):
                resp = await self.llm_backend.generate(full_prompt)
            else:
                resp = self.llm_backend.generate(full_prompt)
            raw_output = (
                getattr(resp, "response_text", None) or getattr(resp, "content", None) or resp
            )

        else:
            raise TypeError(f"Unsupported LLM backend type: {type(self.llm_backend)}")

        # Parse string output to dict if needed
        if isinstance(raw_output, str):
            try:
                data = json.loads(raw_output)
            except json.JSONDecodeError as e:
                raise ValueError(f"LLM produced malformed JSON response: {e}") from e
        elif isinstance(raw_output, dict):
            data = raw_output
        else:
            raise ValueError(f"Unexpected LLM output format: {type(raw_output)}")

        # Validate through Pydantic model
        rec = AIRecommendation.model_validate(data)

        # Check exact evidence span grounding
        span_errors = rec.validate_spans(position.retrieved_evidence)
        if span_errors:
            logger.warning(
                f"Span grounding issues for position {position.position_id}: {'; '.join(span_errors)}"
            )

        return rec

    async def annotate_batch(
        self,
        positions: list[AnnotationPosition],
        batch_size: int = 10,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ) -> list[AIRecommendation]:
        """Process a batch of positions with progress tracking.

        Args:
            positions: List of positions to annotate.
            batch_size: Concurrency chunk size.
            progress_callback: Optional callback receiving (completed_count, total_count).

        Returns:
            List of AIRecommendation objects in same order as input positions.
        """
        results: list[AIRecommendation] = []
        total = len(positions)

        for i in range(0, total, batch_size):
            chunk = positions[i : i + batch_size]
            tasks = [self.annotate_position(pos) for pos in chunk]
            chunk_results = await asyncio.gather(*tasks)
            results.extend(chunk_results)

            if progress_callback:
                progress_callback(len(results), total)

        return results
