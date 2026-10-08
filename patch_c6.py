content = open('tests/e2e/test_v6_c6_image_confirmation_rxnorm.py').read()
content = content.replace('stream_res = client.get(f"/api/v1/stream/{req_id}")\n    events = extract_sse_events(stream_res.text.splitlines())', '''events = []
    with client.stream("GET", f"/api/v1/stream/{req_id}") as stream_res:
        for line in stream_res.iter_lines():
            line = line.strip()
            if line.startswith("event: confirmation_required"):
                events.append({"event": "confirmation_required", "data": {}})
                break
            elif line.startswith("event: medication_candidates_extracted"):
                events.append({"event": "medication_candidates_extracted", "data": {}})
            elif line.startswith("event: error"):
                events.append({"event": "error", "data": {}})
                break
            elif line.startswith("event: stage_update"):
                events.append({"event": "stage_update", "data": {}})''')

# In test_2, it consumes the stream until confirmation_required
content = content.replace('client.get(f"/api/v1/stream/{req_id}")', '''with client.stream("GET", f"/api/v1/stream/{req_id}") as stream_res:
        for line in stream_res.iter_lines():
            if "confirmation_required" in line:
                break''', 1) # Only replace the first one!

# For test_2 remainder, we can leave client.get because it finishes the pipeline!
# Actually, the replacement above replaced the first client.get in 	est_2, which is good.

open('tests/e2e/test_v6_c6_image_confirmation_rxnorm.py', 'w').write(content)
