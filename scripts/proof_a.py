import asyncio
import os
import json
import hashlib
from datetime import datetime, timezone
import uuid
from adaptive_trust_medical_rag.llm_backend import get_backend


async def main():
    os.environ["LLM_MODE"] = "LIVE_LLM"
    os.environ["LLM_PROVIDER"] = "gemini"
    os.environ["LLM_MODEL"] = "gemini-3.6-flash"

    proof_id = "proof_a_" + str(uuid.uuid4())
    data = {"proof_id": proof_id, "execution_status": "NOT_EXECUTED"}

    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set. Execution aborted.")
    else:
        try:
            backend = get_backend()
            prompt = "What is the mechanism of action of Aspirin? Provide a 1-sentence summary."
            print(f"Executing Proof A against {backend.model_name}...")

            result = await backend.generate(prompt)

            data.update(
                {
                    "execution_status": "PASS" if result.status == "SUCCESS" else "FAIL",
                    "provider": result.provider,
                    "model": result.model,
                    "local_execution_id": result.local_execution_id,
                    "request_id": result.request_id,
                    "response_id": result.response_id,
                    "request_started_at": result.request_started_at,
                    "response_received_at": result.response_received_at,
                    "finish_reason": result.finish_reason,
                    "response_hash": result.response_hash,
                    "response_length": result.response_length,
                    "input_tokens": result.input_tokens,
                    "output_tokens": result.output_tokens,
                    "provider_call_latency_ms": result.provider_call_latency_ms,
                    "status": result.status,
                }
            )

            print("Proof A Execution Status:", data["execution_status"])
        except Exception as e:
            print(f"Proof A failed: {e}")
            data["execution_status"] = "FAIL"

    print(json.dumps(data, indent=2))
    os.makedirs("reports/audit", exist_ok=True)
    with open("reports/audit/proof_a_telemetry.json", "w") as f:
        json.dump(data, f, indent=2)


if __name__ == "__main__":
    asyncio.run(main())
