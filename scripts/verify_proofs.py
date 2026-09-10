import json
import hashlib
import uuid
import os
from datetime import datetime


def verify_proof_a(path="reports/audit/proof_a_telemetry.json"):
    if not os.path.exists(path):
        print(f"Proof A file not found: {path}")
        return False

    with open(path, "r") as f:
        data = json.load(f)

    if data.get("execution_status") == "NOT_EXECUTED":
        print("Proof A: NOT_EXECUTED. Verification skipped.")
        return False

    if data.get("execution_status") != "PASS":
        print("Proof A: FAILED execution status.")
        return False

    # 1. UUID Check
    try:
        local_id = data["local_execution_id"]
        uuid.UUID(local_id)
    except Exception:
        print("Proof A: Invalid local_execution_id UUID.")
        return False

    # 2. Timestamp Ordering Check
    try:
        start = datetime.fromisoformat(data["request_started_at"])
        end = datetime.fromisoformat(data["response_received_at"])
        if start > end:
            print("Proof A: Invalid timestamp ordering.")
            return False
    except Exception:
        print("Proof A: Invalid timestamp format.")
        return False

    # 3. Hash Verification
    if data.get("response_text"):
        expected_hash = hashlib.sha256(data["response_text"].encode("utf-8")).hexdigest()
        if expected_hash != data.get("response_hash"):
            print("Proof A: Hash mismatch!")
            return False

    # 4. Provider/Model Check
    if data.get("provider") != "google-genai" or data.get("model") != "gemini-3.6-flash":
        print("Proof A: Invalid provider or model configuration.")
        return False

    print("Proof A: INDEPENDENT VERIFICATION PASS")
    return True


if __name__ == "__main__":
    verify_proof_a()
