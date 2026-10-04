import httpx
import json
import asyncio

async def test_e2e():
    print("Sending POST request to /api/v1/analyze")
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            response = await client.post(
                "http://localhost:8001/api/v1/analyze",
                json={
                    "input_mode": "direct_drugs",
                    "drug_names": ["warfarin overdose"],
                    "patient_context": None
                }
            )
            print(f"Status: {response.status_code}")
            if response.status_code != 200:
                print("Failed to start analysis:", response.text)
                return
            
            data = response.json()
            request_id = data.get("request_id")
            print(f"Request ID: {request_id}")
            
            print(f"Connecting to SSE stream: /api/v1/stream/{request_id}")
            event_name = None
            async with client.stream("GET", f"http://localhost:8001/api/v1/stream/{request_id}") as stream:
                async for line in stream.aiter_lines():
                    if line.startswith("event: "):
                        event_name = line[7:].strip()
                    elif line.startswith("data: "):
                        if not event_name: continue
                        payload = json.loads(line[6:])
                        print(f"Received event: {event_name}")
                        if event_name in ("answer", "abstention", "error"):
                            print("Final payload:")
                            print(json.dumps(payload, indent=2))
                        if event_name == "complete":
                            break
                        event_name = None
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_e2e())
