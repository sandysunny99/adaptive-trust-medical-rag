from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.on_event('startup')
async def startup():
    print('STARTUP FIRED')

client = TestClient(app)
print('Sending request')
client.get('/')
print('Done')
