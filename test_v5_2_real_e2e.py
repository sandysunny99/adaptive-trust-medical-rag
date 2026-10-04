"""V5.2 Real Multi-Provider E2E Validation Script.

Executes real HTTP requests through FastAPI endpoints.
Does NOT directly call LiveMedicalRAGService.
Does NOT monkey-patch retrieval.
Does NOT inject evidence manually.
"""
import httpx
import json
import asyncio
import time
import sys

BASE_URL = "http://localhost:8002"

async def run_medical_e2e(label: str, drugs: list[str], expect_abstention: bool = False):
    """Submit a real POST /api/v1/analyze and consume GET /api/v1/stream/{request_id}."""
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    
    async with httpx.AsyncClient(timeout=120) as client:
        # POST
        print(f"  POST /api/v1/analyze  drugs={drugs}")
        response = await client.post(
            f"{BASE_URL}/api/v1/analyze",
            json={
                "input_mode": "direct_drugs",
                "drug_names": drugs,
                "patient_context": None
            }
        )
        print(f"  HTTP Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  FAIL: {response.text}")
            return None
        
        data = response.json()
        request_id = data["request_id"]
        stream_url = data["stream_url"]
        print(f"  Request ID: {request_id}")
        print(f"  Stream URL: {stream_url}")
        
        # SSE Stream
        print(f"\n  --- SSE Stream ---")
        events = []
        final_payload = None
        final_event_type = None
        
        async with client.stream("GET", f"{BASE_URL}{stream_url}") as stream:
            event_name = None
            async for line in stream.aiter_lines():
                if line.startswith("event: "):
                    event_name = line[7:].strip()
                elif line.startswith("data: ") and event_name:
                    payload = json.loads(line[6:])
                    events.append({"event": event_name, "data": payload})
                    
                    if event_name == "stage_update":
                        stage = payload.get("stage", "?")
                        status = payload.get("status", "?")
                        print(f"    [{stage}] {status}")
                    elif event_name in ("answer", "abstention", "error"):
                        final_event_type = event_name
                        final_payload = payload
                        print(f"    >>> FINAL EVENT: {event_name}")
                    elif event_name == "complete":
                        print(f"    >>> STREAM COMPLETE")
                        break
                    event_name = None
        
        return {
            "label": label,
            "drugs": drugs,
            "request_id": request_id,
            "events": events,
            "final_event": final_event_type,
            "final_payload": final_payload,
            "expect_abstention": expect_abstention,
        }


async def main():
    results = {}
    
    # ============================================================
    # TEST 1: NVIDIA Happy Path (warfarin + aspirin)
    # ============================================================
    nvidia_result = await run_medical_e2e(
        label="NVIDIA: warfarin + aspirin (Happy Path)",
        drugs=["warfarin", "aspirin"],
        expect_abstention=False
    )
    results["nvidia_happy"] = nvidia_result
    
    # ============================================================
    # TEST 2: Controlled Abstention (warfarin overdose)
    # ============================================================
    abstention_result = await run_medical_e2e(
        label="Controlled Abstention: warfarin overdose",
        drugs=["warfarin overdose"],
        expect_abstention=True
    )
    results["abstention"] = abstention_result
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  V5.2 RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for key, r in results.items():
        if r is None:
            print(f"  [{key}] FAIL - No response received")
            continue
            
        fe = r["final_event"]
        if r["expect_abstention"]:
            status = "PASS" if fe == "abstention" else "FAIL"
            print(f"  [{key}] {status} - Expected abstention, got: {fe}")
        else:
            status = "PASS" if fe == "answer" else ("ABSTAINED" if fe == "abstention" else "FAIL")
            print(f"  [{key}] {status} - Final event: {fe}")
            
        if r["final_payload"]:
            fp = r["final_payload"]
            if fe == "answer":
                print(f"    medications: {len(fp.get('medications', []))}")
                print(f"    interactions: {len(fp.get('interactions', []))}")
                print(f"    claims: {len(fp.get('claims', []))}")
                print(f"    evidence: {len(fp.get('evidence', []))}")
                print(f"    gate_decision: {fp.get('gate_decision')}")
                print(f"    conclusion preview: {str(fp.get('conclusion',''))[:100]}...")
            elif fe == "abstention":
                print(f"    reason: {fp.get('reason')}")
                trust = fp.get("trust", {})
                print(f"    trust_score: {trust.get('overall_score')}")
                print(f"    threshold: {trust.get('threshold')}")
                print(f"    risk_class: {trust.get('risk_class')}")
    
    # Write raw results to JSON for inspection
    with open("v5_2_e2e_raw_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Raw results written to v5_2_e2e_raw_results.json")

if __name__ == "__main__":
    asyncio.run(main())
