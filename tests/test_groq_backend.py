import pytest
import httpx
from unittest.mock import patch, MagicMock
from adaptive_trust_medical_rag.llm_backend.groq_backend import GroqBackend

@pytest.mark.asyncio
async def test_groq_rate_limit_parsing():
    backend = GroqBackend(api_key="dummy")
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "test"}, "finish_reason": "stop"}],
        "id": "123",
        "usage": {"prompt_tokens": 10, "completion_tokens": 10}
    }
    mock_response.headers = {
        "x-ratelimit-remaining-requests": "99",
        "x-ratelimit-remaining-tokens": "999",
        "retry-after": "5.5"
    }
    
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await backend.generate("prompt")
        
        assert result.rate_limit is not None
        assert result.rate_limit.remaining_requests == 99
        assert result.rate_limit.remaining_tokens == 999
        assert result.rate_limit.retry_after == 5.5
