import json
import hashlib

manifest_file = 'track_a_annotation/decision_batches/TRACK_A_A_BATCH_003_AUTHORITATIVE_POSITION_MANIFEST.json'
master_file = 'track_a_annotation/annotator_a/TRACK_A_ANNOTATOR_A.jsonl'
registry_file = 'track_a_annotation/manifests/TRACK_A_RESERVED_POSITIONS.json'
staging_file = 'track_a_annotation/decision_batches/TRACK_A_BATCH_003_P11_P60_V6_ADJUDICATION.json'

with open(manifest_file, 'r', encoding='utf-8') as f:
    manifest = json.load(f)

m_recs = {}
with open(master_file, 'r', encoding='utf-8') as f:
    for line in f:
        if line.strip():
            r = json.loads(line)
            m_recs[r['position_id']] = r

with open(registry_file, 'r', encoding='utf-8') as f:
    registry = json.load(f)
    
with open(staging_file, 'r', encoding='utf-8') as f:
    staging = json.load(f)

# Counts
positions = len(staging)
pos_matches = 0
seq_matches = 0
batch_matches = 0
res_matches = 0
query_matches = 0
evidence_matches = 0
fingerprint_matches = 0
legal_labels = 0
legal_grades = 0
exact_literal_spans = 0

semantic_span_pass = 0
semantic_span_fail = 0
semantic_span_review = 0

rationale_pass = 0
rationale_fail = 0
rationale_review = 0

high_review = 0
medium_review = 0
low_review = 0

conf_high = 0
conf_medium = 0
conf_low = 0

counterevidence_present = 0
alternative_considered = 0

auto_labels = 0
duplicates = 0
out_of_window = 0
out_of_batch = 0
schema_errors = 0

seen_pids = set()
legal_label_set = {"RELEVANT", "PARTIALLY_RELEVANT", "IRRELEVANT", "INSUFFICIENT_INFORMATION", "AMBIGUOUS"}
legal_grade_set = {2, 1, 0, None}

for rec in staging:
    pid = rec['position_id']
    if pid in seen_pids:
        duplicates += 1
    seen_pids.add(pid)
    seq = rec['sequence_number']
    
    if pid not in m_recs:
        schema_errors += 1
        continue
        
    m_rec = m_recs[pid]
    reg = registry.get(pid, {})
    
    if m_rec['position_id'] == pid: pos_matches += 1
    
    man_seq = next((p['sequence_number'] for p in manifest if p['position_id'] == pid), None)
    if man_seq == seq: seq_matches += 1
    else: out_of_window += 1
    
    if rec['batch_id'] == "TRACK_A_A_BATCH_003" and reg.get('batch_id') == "TRACK_A_A_BATCH_003": batch_matches += 1
    else: out_of_batch += 1
        
    if reg.get('reservation_status') == "RESERVED": res_matches += 1
    if rec['query_analysis']['query_intent_summary']: query_matches += 1
    
    ev = m_rec['retrieved_evidence']
    s_sha256 = hashlib.sha256(json.dumps({"position_id": pid, "query_text": m_rec['query_text'], "retrieved_evidence": ev}, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode('utf-8')).hexdigest()
    if s_sha256 == rec['source_record_sha256']:
        fingerprint_matches += 1
        evidence_matches += 1
        
    if rec['proposed_label'] in legal_label_set: legal_labels += 1
    if rec['proposed_grade'] in legal_grade_set: legal_grades += 1
    
    span = rec['proposed_evidence_span']
    idx = ev.find(span)
    if idx >= 0 and rec['span_character_index'] == idx and rec['span_length'] == len(span):
        exact_literal_spans += 1
        
    sem_sp = rec['semantic_span_support']
    if sem_sp == "PASS": semantic_span_pass += 1
    elif sem_sp == "FAIL": semantic_span_fail += 1
    else: semantic_span_review += 1
    
    rat_c = rec['rationale_evidence_consistency']
    if rat_c == "PASS": rationale_pass += 1
    elif rat_c == "FAIL": rationale_fail += 1
    else: rationale_review += 1
        
    rp = rec['review_priority']
    if rp == "HIGH": high_review += 1
    elif rp == "MEDIUM": medium_review += 1
    elif rp == "LOW": low_review += 1
    
    conf = rec['confidence']
    if conf == "HIGH": conf_high += 1
    elif conf == "MEDIUM": conf_medium += 1
    elif conf == "LOW": conf_low += 1
    
    if len(rec['counterevidence']) > 0: counterevidence_present += 1
    if rec['alternative_label_considered'] is not None: alternative_considered += 1
    
    if rec['human_final_label'] is not None: auto_labels += 1

report = f"""# TRACK_A_BATCH_003_P11_P60_V6_VALIDATION_REPORT

Positions = {positions}
Position ID matches = {pos_matches}
Sequence matches = {seq_matches}
Batch matches = {batch_matches}
Reservation matches = {res_matches}
Query matches = {query_matches}
Evidence matches = {evidence_matches}
Fingerprint matches = {fingerprint_matches}

Legal labels = {legal_labels}
Legal grades = {legal_grades}

Exact literal spans = {exact_literal_spans}

Semantic span PASS = {semantic_span_pass}
Semantic span FAIL = {semantic_span_fail}
Semantic span REVIEW = {semantic_span_review}

Rationale PASS = {rationale_pass}
Rationale FAIL = {rationale_fail}
Rationale REVIEW = {rationale_review}

High priority = {high_review}
Medium priority = {medium_review}
Low priority = {low_review}

Confidence HIGH = {conf_high}
Confidence MEDIUM = {conf_medium}
Confidence LOW = {conf_low}

Counterevidence present = {counterevidence_present}
Alternative label considered = {alternative_considered}

Automatic labels = {auto_labels}
Duplicate records = {duplicates}
Out-of-window = {out_of_window}
Out-of-batch = {out_of_batch}
Schema errors = {schema_errors}
"""

with open('track_a_annotation/decision_batches/TRACK_A_BATCH_003_P11_P60_V6_VALIDATION_REPORT.md', 'w', encoding='utf-8') as f:
    f.write(report)

print("INDEPENDENT_VALIDATOR_V6_COMPLETE")
