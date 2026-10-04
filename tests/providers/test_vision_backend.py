import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import httpx
from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import OpenAIVisionBackend
from adaptive_trust_medical_rag.llm_backend.vision_interfaces import ExtractionConfidence
from adaptive_trust_medical_rag.llm_routing.types import FailureClass
from adaptive_trust_medical_rag.llm_backend.interfaces import ModelExecutionError
import json

@pytest.fixture
def vision_backend():
    return OpenAIVisionBackend(
        base_url="https://fake.nvidia.com/v1",
        api_key="fake_key",
        model_name="meta/llama-3.2-11b-vision-instruct"
    )

class MockResponse:
    def __init__(self, status_code, json_data=None, text=""):
        self.status_code = status_code
        self._json_data = json_data
        self.text = text
    def json(self):
        return self._json_data

@pytest.mark.asyncio
async def test_vision_extraction_success(vision_backend):
    mock_json = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "raw_text": "Warfarin 5mg",
                        "candidate_medications": [
                            {
                                "raw_text": "Warfarin",
                                "normalized_text": "warfarin",
                                "confidence": "HIGH"
                            }
                        ],
                        "warnings": []
                    })
                }
            }
        ]
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MockResponse(200, json_data=mock_json)
        
        result = await vision_backend.extract_medications(b"fakeimage", "image/jpeg")
        
        assert result.raw_text == "Warfarin 5mg"
        assert len(result.candidate_medications) == 1
        assert result.candidate_medications[0].raw_text == "Warfarin"
        assert result.candidate_medications[0].confidence == ExtractionConfidence.HIGH

@pytest.mark.asyncio
async def test_vision_extraction_auth_error(vision_backend):
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MockResponse(401, text="Unauthorized")
        
        with pytest.raises(ModelExecutionError) as exc_info:
            await vision_backend.extract_medications(b"fakeimage", "image/jpeg")
            
        assert exc_info.value.failure_class == FailureClass.AUTHENTICATION

@pytest.mark.asyncio
async def test_vision_extraction_schema_error(vision_backend):
    mock_json = {
        "choices": [
            {
                "message": {
                    "content": "Not JSON at all"
                }
            }
        ]
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MockResponse(200, json_data=mock_json)
        
        with pytest.raises(ModelExecutionError) as exc_info:
            await vision_backend.extract_medications(b"fakeimage", "image/jpeg")
            
        assert exc_info.value.failure_class == FailureClass.SCHEMA_ERROR

@pytest.mark.asyncio
async def test_vision_extraction_markdown_stripped(vision_backend):
    mock_json = {
        "choices": [
            {
                "message": {
                    "content": "```json\n" + json.dumps({
                        "raw_text": "Aspirin 81mg",
                        "candidate_medications": [],
                        "warnings": []
                    }) + "\n```"
                }
            }
        ]
    }
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MockResponse(200, json_data=mock_json)
        
        result = await vision_backend.extract_medications(b"fakeimage", "image/jpeg")
        assert result.raw_text == "Aspirin 81mg"
