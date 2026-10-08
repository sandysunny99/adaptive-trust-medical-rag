import time
import requests
import subprocess
import sys
import threading
import os

def run_server():
    env = os.environ.copy()
    env["PYTHONPATH"] = "src"
    subprocess.run([sys.executable, "-m", "uvicorn", "adaptive_trust_medical_rag.api.app:app", "--port", "8000"], env=env)

# Start server
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# Wait for startup
print("Waiting for server to start...")
start_time = time.time()
while True:
    try:
        requests.get("http://127.0.0.1:8000/health")
        break
    except:
        time.sleep(0.1)
        if time.time() - start_time > 30:
            print("Server failed to start")
            sys.exit(1)
startup_time = time.time() - start_time
print(f"Startup Time: {startup_time:.2f} seconds")

# Test health
health_start = time.time()
res = requests.get("http://127.0.0.1:8000/health")
health_time = time.time() - health_start
print(f"Health Response Time: {health_time:.4f} seconds")
print(f"Health Status: {res.status_code}")

# Test first analyze
analyze_start = time.time()
payload = {
    "drug_names": ["warfarin", "aspirin"],
    "input_mode": "direct_drugs"
}
res2 = requests.post("http://127.0.0.1:8000/api/v1/analyze", json=payload)
req_id = res2.json().get("request_id")
print(f"Analyze request_id: {req_id}")

stream_start = time.time()
events_received = []
try:
    with requests.get(f"http://127.0.0.1:8000/api/v1/stream/{req_id}", stream=True, timeout=30) as r:
        for line in r.iter_lines():
            if line:
                events_received.append(line.decode('utf-8'))
                if b"stage_update" in line and b"complete" in line and b"retrieving" in line:
                    break
except Exception as e:
    print(f"Stream error: {e}")

stream_time = time.time() - stream_start
print(f"First real inference time (to retrieval): {stream_time:.4f} seconds")
print(f"Events received: {len(events_received)}")
