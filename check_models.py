import asyncio
import os
import httpx
from dotenv import load_dotenv

load_dotenv('.env')

async def check_groq():
    key = os.environ.get('GROQ_API_KEY')
    async with httpx.AsyncClient() as client:
        res = await client.get('https://api.groq.com/openai/v1/models', headers={'Authorization': f'Bearer {key}'})
        data = res.json()
        if 'data' in data:
            print("Groq Models:", [m['id'] for m in data['data']])
        else:
            print("Error:", data)

asyncio.run(check_groq())
