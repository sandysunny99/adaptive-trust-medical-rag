import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv('.env')
token = os.environ.get('HF_TOKEN')

async def test_dns():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get('https://huggingface.co/api/models')
            print('HF API HTTP:', res.status_code)
    except Exception as e:
        print('HF API HTTP ERROR:', e)

asyncio.run(test_dns())
