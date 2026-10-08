import time
import asyncio
from httpx import AsyncClient, ASGITransport
from adaptive_trust_medical_rag.api.app import create_app

app = create_app()

async def run_test():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        t0 = time.time()
        print('1. Checking /health (should be instant)')
        res = await client.get("/health")
        t1 = time.time()
        print(f"   Status: {res.status_code}, Time: {t1-t0:.4f}s")
        assert t1-t0 < 1.0, "Health check took too long!"
        
        print('2. Calling /api/v1/analyze (should trigger lazy load of models)')
        t2 = time.time()
        req_data = {
            "drug_names": ["Aspirin"],
            "patient_context": {}
        }
        res2 = await client.post("/api/v1/analyze", json=req_data)
        t3 = time.time()
        print(f"   Status: {res2.status_code}, Time: {t3-t2:.4f}s")
        
        req_id = res2.json().get("request_id")
        if req_id:
            # We hit the stream endpoint, which triggers execute
            res3 = await client.get(f"/api/v1/stream/{req_id}")
            t4 = time.time()
            print(f"   Stream check: {res3.status_code}, Time: {t4-t3:.4f}s")
            
        print('Done.')

asyncio.run(run_test())
