import asyncio
import io
from PIL import Image
from adaptive_trust_medical_rag.core.config import settings
from adaptive_trust_medical_rag.llm_backend.openai_vision_backend import OpenAIVisionBackend
import os

async def test_real_nvidia_vision():
    # Force dotenv load in case it wasn't
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        print("FAIL: No NVIDIA_API_KEY")
        return
        
    backend = OpenAIVisionBackend(
        provider_name="nvidia_vision",
        base_url="https://integrate.api.nvidia.com/v1",
        api_key=api_key,
        model_name="meta/llama-3.2-11b-vision-instruct"
    )
    
    # Create synthetic test image
    img = Image.new("RGB", (400, 200), color="white")
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(img)
    d.text((10,10), "Warfarin 5 mg\nAspirin 81 mg", fill=(0,0,0))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    image_bytes = buf.getvalue()
    
    print("Sending real image to NVIDIA...")
    try:
        res = await backend.extract_medications(image_bytes, "image/jpeg")
        print(f"PASS: Real NVIDIA Vision Request successful.")
        print(f"Extracted raw text: {res.raw_text}")
        for c in res.candidate_medications:
            print(f"Candidate: {c.raw_text}, Conf: {c.confidence.value}")
    except Exception as e:
        print(f"FAIL: Request failed with {e}")

if __name__ == "__main__":
    asyncio.run(test_real_nvidia_vision())
