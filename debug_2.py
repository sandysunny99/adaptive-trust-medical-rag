import pytest
import io
import json
import asyncio
from httpx import AsyncClient, ASGITransport
from PIL import Image

from adaptive_trust_medical_rag.api.app import app

def create_test_image(size=(100, 100)):
    img = Image.new("RGB", size, color="white")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()

async def test_debug_2():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        file_bytes = create_test_image()
        files = {"image": ("prescription.jpg", file_bytes, "image/jpeg")}
        post_res = await client.post("/api/v1/analyze/prescription", files=files)
        req_id = post_res.json()["request_id"]
        stream_task = asyncio.create_task(client.get(f"/api/v1/stream/{req_id}"))
        await asyncio.sleep(0.5)
        confirm_payload = {
            "confirmed_medications": [
                {"name": "Warfarin", "status": "CONFIRMED", "source": "VISION", "raw_detected_name": "Warfarin 5mg"}
            ]
        }
        await client.post(f"/api/v1/analyze/{req_id}/confirm", json=confirm_payload)
        res = await stream_task
        print("EVENTS:", res.text)

asyncio.run(test_debug_2())
