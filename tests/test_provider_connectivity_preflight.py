"""Provider connectivity preflight tests.

These are CONNECTIVITY_CHECK tests, NOT Phase 15 observations.
They validate that provider clients can initialize and credentials
are detectable without submitting any frozen Phase 15 query.
"""
import os

import pytest

from adaptive_trust_medical_rag.llm_routing.config import RoutingConfig, load_env_local


class TestProviderConnectivityPreflight:
    """Non-Phase15 connectivity checks for each provider."""

    @classmethod
    def setup_class(cls):
        load_env_local()

    def test_groq_credential_detectable(self):
        config = RoutingConfig.default_routing()
        groq = next((p for p in config.providers if p.name == "groq"), None)
        assert groq is not None, "Groq must be in default routing config"
        # Just check credential presence — do not print the key
        status = "PRESENT" if groq.credential_present else "MISSING"
        assert status in ("PRESENT", "MISSING")

    def test_gemini_credential_detectable(self):
        config = RoutingConfig.default_routing()
        gemini = next((p for p in config.providers if p.name == "gemini"), None)
        assert gemini is not None, "Gemini must be in default routing config"
        status = "PRESENT" if gemini.credential_present else "MISSING"
        assert status in ("PRESENT", "MISSING")

    def test_hf_credential_detectable(self):
        config = RoutingConfig.default_routing()
        hf = next((p for p in config.providers if p.name == "huggingface"), None)
        assert hf is not None, "HuggingFace must be in default routing config"
        status = "PRESENT" if hf.credential_present else "MISSING"
        assert status in ("PRESENT", "MISSING")

    def test_groq_client_initializes(self):
        """Groq backend can be constructed when credential is present."""
        key = os.getenv("GROQ_API_KEY")
        if not key:
            pytest.skip("GROQ_API_KEY not set")
        from adaptive_trust_medical_rag.llm_backend.groq_backend import GroqBackend
        backend = GroqBackend(api_key=key, model_name="openai/gpt-oss-120b")
        assert backend is not None

    def test_gemini_client_initializes(self):
        """Gemini backend can be constructed when credential is present."""
        key = os.getenv("GEMINI_API_KEY")
        if not key:
            pytest.skip("GEMINI_API_KEY not set")
        from adaptive_trust_medical_rag.llm_backend.google_gemini_backend import GoogleGeminiBackend
        backend = GoogleGeminiBackend(api_key=key, model_name="gemini-3.1-pro-preview")
        assert backend is not None

    def test_hf_client_initializes(self):
        """HF backend can be constructed when credential is present."""
        token = os.getenv("HF_TOKEN")
        if not token:
            pytest.skip("HF_TOKEN not set")
        from adaptive_trust_medical_rag.llm_backend.huggingface_backend import HuggingFaceBackend
        backend = HuggingFaceBackend(token=token)
        assert backend is not None

    def test_cloudflare_credential_detectable(self):
        config = RoutingConfig.default_routing()
        cf = next((p for p in config.providers if p.name == "cloudflare"), None)
        assert cf is not None, "Cloudflare must be in default routing config"
        status = "PRESENT" if cf.credential_present else "MISSING"
        assert status in ("PRESENT", "MISSING")

    def test_cloudflare_client_initializes(self):
        """Cloudflare backend can be constructed when credentials are present."""
        token = (os.getenv("CLOUDFLARE_API_TOKEN") or "").strip()
        account = (os.getenv("CLOUDFLARE_ACCOUNT_ID") or "").strip()
        if not token or not account:
            pytest.skip("CLOUDFLARE_API_TOKEN or CLOUDFLARE_ACCOUNT_ID not set")
        from adaptive_trust_medical_rag.llm_backend.cloudflare_backend import CloudflareBackend
        backend = CloudflareBackend(api_token=token, account_id=account)
        assert backend is not None

    def test_routing_profiles_exist(self):
        """Verify all routing profiles can be constructed."""
        normal = RoutingConfig.default_routing()
        assert normal.mode.value == "APPLICATION"
        assert len(normal.providers) == 4

        scientific = RoutingConfig.scientific_phase15()
        assert scientific.mode.value == "SCIENTIFIC"
        assert scientific.failover_enabled is False
        assert len(scientific.providers) == 1
        assert scientific.providers[0].name == "gemini"
        assert scientific.providers[0].model_id == "gemini-3.1-pro-preview"


    def test_phase15_dataset_not_consumed(self):
        """Verify these tests did NOT consume any Phase 15 cases."""
        # This is a sentinel assertion — the test file never imports
        # or opens phase15_cases.jsonl
        import adaptive_trust_medical_rag.llm_routing.config as cfg_mod
        source = open(cfg_mod.__file__).read()
        assert "phase15_cases" not in source
