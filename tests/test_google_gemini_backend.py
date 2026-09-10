import asyncio
from unittest.mock import MagicMock, patch

import pytest
from google.genai.types import (
    Candidate,
    Content,
    FinishReason,
    GenerateContentResponse,
    GenerateContentResponseUsageMetadata,
    Part,
)

from adaptive_trust_medical_rag.common.model_result import (
    ModelExecutionError,
)
from adaptive_trust_medical_rag.llm_backend.google_gemini_backend import GoogleGeminiBackend


@pytest.fixture
def mock_gemini_client():
    with patch(
        "adaptive_trust_medical_rag.llm_backend.google_gemini_backend.genai.Client"
    ) as mock_client_cls:
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        yield mock_client


@pytest.mark.asyncio
async def test_gemini_backend_success(mock_gemini_client):
    backend = GoogleGeminiBackend(api_key="test-key", model_name="gemini-test")

    mock_usage = GenerateContentResponseUsageMetadata(
        prompt_token_count=10, candidates_token_count=20, total_token_count=30
    )
    mock_part = Part(text="This is a real generated response.")
    mock_content = Content(parts=[mock_part])
    mock_candidate = Candidate(finish_reason=FinishReason.STOP, content=mock_content)
    mock_response = GenerateContentResponse(
        response_id="prov-123",
        usage_metadata=mock_usage,
        candidates=[mock_candidate],
        model_version="gemini-test-1",
    )

    async def mock_generate_content(*args, **kwargs):
        return mock_response

    backend.client.aio.models.generate_content = mock_generate_content

    result = await backend.generate("Hello")
    assert result.provider == "gemini"
    assert result.model == "gemini-test"
    assert result.response_text == "This is a real generated response."
    assert result.input_tokens == 10
    assert result.output_tokens == 20
    assert result.response_id == "prov-123"
    assert result.request_id is None
    assert result.local_execution_id is not None
    assert result.finish_reason == "STOP"
    assert result.status == "SUCCESS"


@pytest.mark.asyncio
async def test_gemini_backend_empty_response(mock_gemini_client):
    backend = GoogleGeminiBackend(api_key="test-key", model_name="gemini-test")

    mock_part = Part(text="")
    mock_content = Content(parts=[mock_part])
    mock_candidate = Candidate(content=mock_content)
    mock_response = GenerateContentResponse(
        candidates=[mock_candidate],
    )

    async def mock_generate_content(*args, **kwargs):
        return mock_response

    backend.client.aio.models.generate_content = mock_generate_content

    with pytest.raises(ModelExecutionError) as exc:
        await backend.generate("Hello")
    assert exc.value.status_code == "EMPTY_RESPONSE"


@pytest.mark.asyncio
async def test_gemini_backend_strict_timeout(mock_gemini_client):
    backend = GoogleGeminiBackend(api_key="test-key", model_name="gemini-test")

    async def mock_generate_content(*args, **kwargs):
        await asyncio.sleep(40.0)  # wait long enough to trigger wait_for timeout

    backend.client.aio.models.generate_content = mock_generate_content

    # use small wait_for in test
    with patch(
        "adaptive_trust_medical_rag.llm_backend.google_gemini_backend.asyncio.wait_for",
        side_effect=asyncio.TimeoutError,
    ):
        with pytest.raises(ModelExecutionError) as exc:
            await backend.generate("Hello")
        assert exc.value.status_code == "TIMEOUT"
