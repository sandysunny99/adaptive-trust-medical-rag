import asyncio
import os
from dotenv import load_dotenv
from adaptive_trust_medical_rag.llm_backend.openai_compatible_backend import OpenAICompatibleBackend

load_dotenv('.env')

async def test_schema():
    cf_account = os.environ.get('CLOUDFLARE_ACCOUNT_ID')
    backend = OpenAICompatibleBackend(
        provider_name="Cloudflare",
        base_url=f"https://api.cloudflare.com/client/v4/accounts/{cf_account}/ai/v1",
        api_key=os.environ.get("CLOUDFLARE_API_TOKEN"),
        model_name="@cf/meta/llama-3.3-70b-instruct-fp8-fast"
    )
    
    schema = {
        "type": "json_schema",
        "json_schema": {
            "name": "VerificationReport",
            "schema": {
                "type": "object",
                "properties": {
                    "claims": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "text": {"type": "string"},
                                "is_supported": {"type": "boolean"},
                                "citations": {
                                    "type": "array",
                                    "items": {"type": "integer"}
                                }
                            },
                            "required": ["text", "is_supported", "citations"]
                        }
                    },
                    "final_decision": {"type": "string", "enum": ["release", "abstain"]}
                },
                "required": ["claims", "final_decision"]
            }
        }
    }
    
    prompt = '''
    Evaluate this medical claim: "Patient took Aspirin and had no reaction."
    Evidence: None.
    Provide a VerificationReport matching the schema.
    '''
    
    try:
        res = await backend.generate_structured(prompt, response_format=schema)
        print("Complex schema success! Output:")
        print(res.structured_output)
    except Exception as e:
        print("Complex schema fail:", e)

asyncio.run(test_schema())
