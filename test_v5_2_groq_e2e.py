"""V5.2 Groq E2E Validation - port 8003."""
import httpx
import json
import asyncio

BASE_URL = "http://localhost:8003"

async def run_medical_e2e(label, drugs, expect_abstention=False):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    
    async with httpx.AsyncClient(timeout=120) as client:
        response = await client.post(
            f"{BASE_URL}/api/v1/analyze",
            json={"input_mode": "direct_drugs", "drug_names": drugs, "patient_context": None}
        )
        print(f"  HTTP Status: {response.status_code}")
        if response.status_code != 200:
            print(f"  FAIL: {response.text}")
            return None
        
        data = response.json()
        request_id = data["request_id"]
        print(f"  Request ID: {request_id}")
        
        events = []
        final_payload = None
        final_event_type = None
        
        async with client.stream("GET", f"{BASE_URL}/api/v1/stream/{request_id}") as stream:
            event_name = None
            async for line in stream.aiter_lines():
                if line.startswith("event: "):
                    event_name = line[7:].strip()
                elif line.startswith("data: ") and event_name:
                    payload = json.loads(line[6:])
                    events.append({"event": event_name, "data": payload})
                    if event_name == "stage_update":
                        print(f"    [{payload.get('stage','?')}] {payload.get('status','?')}")
                    elif event_name in ("answer", "abstention", "error"):
                        final_event_type = event_name
                        final_payload = payload
                        print(f"    >>> FINAL EVENT: {event_name}")
                    elif event_name == "complete":
                        print(f"    >>> STREAM COMPLETE")
                        break
                    event_name = None
        
        return {
            "label": label, "drugs": drugs, "request_id": request_id,
            "events": events, "final_event": final_event_type,
            "final_payload": final_payload, "expect_abstention": expect_abstention,
        }

async def main():
    results = {}
    
    # Groq happy path
    results["groq_happy"] = await run_medical_e2e(
        "GROQ: warfarin + aspirin (Happy Path)", ["warfarin", "aspirin"])
    
    # Groq abstention
    results["groq_abstention"] = await run_medical_e2e(
        "GROQ: warfarin overdose (Controlled Abstention)", ["warfarin overdose"], True)
    
    print(f"\n{'='*60}")
    print(f"  GROQ V5.2 RESULTS SUMMARY")
    print(f"{'='*60}")
    
    for key, r in results.items():
        if r is None:
            print(f"  [{key}] FAIL - No response")
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
                print(f"    conclusion: {repr(fp.get('conclusion',''))[:200]}")
            elif fe == "abstention":
                trust = fp.get("trust", {})
                print(f"    reason: {fp.get('reason')}")
                print(f"    trust: {trust.get('overall_score')}, threshold: {trust.get('threshold')}, risk: {trust.get('risk_class')}")
    
    with open("v5_2_groq_e2e_raw_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Raw results written to v5_2_groq_e2e_raw_results.json")

if __name__ == "__main__":
    asyncio.run(main())
