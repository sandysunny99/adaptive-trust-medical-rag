import json
lines = open(r'C:\Users\sunny\.gemini\antigravity\brain\0cfc1b71-0ce2-4c00-9445-519329331bb1\.system_generated\logs\transcript.jsonl').readlines()
for line in lines[-5:]:
    print(line[:200])
