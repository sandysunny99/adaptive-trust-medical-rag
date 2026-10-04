import json
import os
import sys

sys.path.insert(0, os.path.abspath('src'))
from adaptive_trust_medical_rag.llm_backend.pilot_adapter import LLMAdapter

def run_test():
    adapter = LLMAdapter(provider="gemini", credentials_env_key="GEMINI_API_KEY")
    
    # Non-medical transport test input
    system_prompt = "Return valid JSON according to the supplied schema."
    user_prompt = "Return status SUCCESS."
    evidence_text = "Paris is the capital of France."
    schema = {"status": "string"}
    
    print("Executing missing-credentials transport test...")
    result = adapter.generate_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        evidence_text=evidence_text,
        schema=schema
    )
    
    out_path = "track_a_annotation/decision_batches/TRACK_A_LLM_TRANSPORT_TEST_V1.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        
    print(f"Transport test generated: {out_path}")
    print(f"Success: {result['success']}")
    print(f"Error Type: {result.get('error_type')}")
    
if __name__ == "__main__":
    run_test()
