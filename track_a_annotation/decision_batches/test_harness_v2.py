import json
import os
import sys

sys.path.insert(0, os.path.abspath('src'))
from adaptive_trust_medical_rag.llm_backend.pilot_adapter import LLMProviderAdapter

def run_test():
    adapter = LLMProviderAdapter(execution_mode="FREELLMAPI_GATEWAY", model="llama3-8b-8192")
    
    system_prompt = "Return valid JSON according to the supplied schema."
    user_prompt = "Return status SUCCESS."
    evidence_text = "Paris is the capital of France."
    schema = {"status": "string"}
    
    print("Executing FreeLLMAPI gateway negative path transport test...")
    result = adapter.generate_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        schema=schema,
        generation_config={"evidence_text": evidence_text}
    )
    
    out_dir = "track_a_annotation/decision_batches"
    os.makedirs(out_dir, exist_ok=True)
    out_path = f"{out_dir}/TRACK_A_LLM_LIVE_TRANSPORT_TEST_V2.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2)
        
    print(f"Transport test generated: {out_path}")
    print(f"Success: {result['success']}")
    print(f"Error Type: {result.get('error_type')}")
    
if __name__ == "__main__":
    run_test()
