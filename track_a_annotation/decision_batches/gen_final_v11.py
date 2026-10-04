import json
import hashlib
import os
import sys
from unittest.mock import patch, Mock

out_dir = "track_a_annotation/decision_batches"
sys.path.insert(0, os.path.abspath('src'))
from adaptive_trust_medical_rag.llm_backend.pilot_adapter import LLMProviderAdapter

# Mock Setup
os.environ["FREELLMAPI_API_KEY"] = "fake_key_for_integration_test"
adapter = LLMProviderAdapter(execution_mode="FREELLMAPI_GATEWAY", model="test")

current_mock_payload = ""

def mocked_requests_post(*args, **kwargs):
    resp = Mock()
    resp.status_code = 200
    resp.headers = {"X-Routed-Via": "MockProvider", "X-Fallback-Attempts": "0", "x-request-id": "mock_id"}
    resp.json.return_value = {"choices": [{"message": {"content": current_mock_payload}}]}
    return resp

def run_integration_test(name, payload_dict, expected_error=None, evidence="This is the exact evidence provided to the model."):
    global current_mock_payload
    current_mock_payload = json.dumps(payload_dict)
    
    with open(f"{out_dir}/TRACK_A_ADJUDICATION_SCHEMA_FINAL_V1.json", "r", encoding="utf-8") as f:
        schema = json.load(f)
        
    with patch('requests.post', side_effect=mocked_requests_post):
        result = adapter.generate_structured(
            system_prompt="sys", 
            user_prompt="usr", 
            schema=schema, 
            generation_config={"evidence_text": evidence}
        )
        
    actual_error = result.get("error_type")
    
    # expected_error None means we expect SUCCESS
    if expected_error is None and result["success"] == True:
        passed = True
    elif expected_error == actual_error:
        passed = True
    else:
        passed = False
        
    return {
        "Test": name,
        "Execution path": "LLMProviderAdapter.generate_structured()",
        "Input condition": f"Mocked JSON returning specified payload",
        "Expected result": expected_error or "SUCCESS",
        "Actual result": actual_error or "SUCCESS",
        "Pass/Fail": "PASS" if passed else "FAIL"
    }

base_payload = {
    "query_entities": ["drugA"],
    "requested_property": "interaction",
    "requested_relation": "concomitant",
    "requested_outcome": "bleeding",
    "entity_alignment": "EXACT",
    "relationship_alignment": "EXACT",
    "relationship_polarity": "POSITIVE",
    "outcome_alignment": "EXACT",
    "outcome_polarity": "POSITIVE",
    "evidence_claims": [],
    "supported_claims": [],
    "unsupported_claims": [],
    "missing_information": [],
    "counterevidence": [],
    "uncertainties": [],
    "best_supporting_span": "exact evidence",
    "proposed_label": "RELEVANT",
    "proposed_grade": 2,
    "proposed_rationale": "rationale",
    "confidence": "HIGH",
    "alternative_label_considered": None
}

def p_mod(**kwargs):
    p = base_payload.copy()
    p.update(kwargs)
    return p

integration_results = []

# 3. LABEL/GRADE PRODUCTION-PATH TESTS
integration_results.append(run_integration_test("A. RELEVANT + grade 2 -> ACCEPT", p_mod(proposed_label="RELEVANT", proposed_grade=2)))
integration_results.append(run_integration_test("B. RELEVANT + grade 1 -> REJECT", p_mod(proposed_label="RELEVANT", proposed_grade=1), "SEMANTIC_SCHEMA_CONSISTENCY_FAILED"))
integration_results.append(run_integration_test("C. PARTIALLY_RELEVANT + grade 1 -> ACCEPT", p_mod(proposed_label="PARTIALLY_RELEVANT", proposed_grade=1)))
integration_results.append(run_integration_test("D. PARTIALLY_RELEVANT + grade 2 -> REJECT", p_mod(proposed_label="PARTIALLY_RELEVANT", proposed_grade=2), "SEMANTIC_SCHEMA_CONSISTENCY_FAILED"))
integration_results.append(run_integration_test("E. IRRELEVANT + grade 0 -> ACCEPT", p_mod(proposed_label="IRRELEVANT", proposed_grade=0, best_supporting_span="")))
integration_results.append(run_integration_test("F. IRRELEVANT + grade 1 -> REJECT", p_mod(proposed_label="IRRELEVANT", proposed_grade=1, best_supporting_span=""), "SEMANTIC_SCHEMA_CONSISTENCY_FAILED"))
integration_results.append(run_integration_test("G. INSUFFICIENT_INFORMATION + grade 0 -> ACCEPT", p_mod(proposed_label="INSUFFICIENT_INFORMATION", proposed_grade=0, best_supporting_span="")))
integration_results.append(run_integration_test("H. INSUFFICIENT_INFORMATION + grade 2 -> REJECT", p_mod(proposed_label="INSUFFICIENT_INFORMATION", proposed_grade=2, best_supporting_span=""), "SEMANTIC_SCHEMA_CONSISTENCY_FAILED"))
integration_results.append(run_integration_test("I. AMBIGUOUS + null -> ACCEPT", p_mod(proposed_label="AMBIGUOUS", proposed_grade=None, best_supporting_span="")))
integration_results.append(run_integration_test("J. AMBIGUOUS + 0 -> REJECT", p_mod(proposed_label="AMBIGUOUS", proposed_grade=0, best_supporting_span=""), "SEMANTIC_SCHEMA_CONSISTENCY_FAILED"))

# 4. EXACT SPAN PRODUCTION-PATH TESTS
ev_text = "This is the exact evidence provided to the model."
integration_results.append(run_integration_test("A. best_span=exact evidence -> ACCEPT", p_mod(best_supporting_span="exact evidence"), None, ev_text))
integration_results.append(run_integration_test("B. best_span=similar evidence -> REJECT", p_mod(best_supporting_span="similar evidence"), "SPAN_VALIDATION_FAILED", ev_text))
integration_results.append(run_integration_test("C. best_span=completely fake span -> REJECT", p_mod(best_supporting_span="completely fake span"), "SPAN_VALIDATION_FAILED", ev_text))
integration_results.append(run_integration_test("D. IRRELEVANT + empty best_span -> ACCEPT", p_mod(proposed_label="IRRELEVANT", proposed_grade=0, best_supporting_span=""), None, ev_text))
integration_results.append(run_integration_test("E. RELEVANT + empty best_span -> REJECT", p_mod(proposed_label="RELEVANT", proposed_grade=2, best_supporting_span=""), "SPAN_VALIDATION_FAILED", ev_text))
integration_results.append(run_integration_test("F. PARTIALLY_RELEVANT + empty best_span -> REJECT", p_mod(proposed_label="PARTIALLY_RELEVANT", proposed_grade=1, best_supporting_span=""), "SPAN_VALIDATION_FAILED", ev_text))

# claims tests
integration_results.append(run_integration_test(
    "A. evidence claims: exact evidence span -> ACCEPT", 
    p_mod(evidence_claims=[{"claim_text":"x", "evidence_span":"provided to", "claim_type":"OTHER", "polarity":"POSITIVE"}]), 
    None, ev_text
))
integration_results.append(run_integration_test(
    "B. evidence claims: paraphrased span -> REJECT", 
    p_mod(evidence_claims=[{"claim_text":"x", "evidence_span":"given to", "claim_type":"OTHER", "polarity":"POSITIVE"}]), 
    "SPAN_VALIDATION_FAILED", ev_text
))
integration_results.append(run_integration_test(
    "C. evidence claims: invented span -> REJECT", 
    p_mod(evidence_claims=[{"claim_text":"x", "evidence_span":"fake", "claim_type":"OTHER", "polarity":"POSITIVE"}]), 
    "SPAN_VALIDATION_FAILED", ev_text
))
integration_results.append(run_integration_test(
    "D. multiple valid exact spans -> ACCEPT", 
    p_mod(evidence_claims=[
        {"claim_text":"x", "evidence_span":"provided to", "claim_type":"OTHER", "polarity":"POSITIVE"},
        {"claim_text":"y", "evidence_span":"exact evidence", "claim_type":"OTHER", "polarity":"POSITIVE"}
    ]), 
    None, ev_text
))

md_out = "# TRACK_A_LLM_REAL_ADAPTER_INTEGRATION_TEST_V1\n\n"
md_out += "All tests explicitly use REAL generate_structured() = YES, HTTP NETWORK CALL = NO, REAL LLM = NO.\n\n"
md_out += "| Test | Execution path | Input condition | Expected result | Actual result | Pass/Fail |\n"
md_out += "|---|---|---|---|---|---|\n"
for r in integration_results:
    md_out += f"| {r['Test']} | {r['Execution path']} | {r['Input condition']} | {r['Expected result']} | {r['Actual result']} | {r['Pass/Fail']} |\n"

with open(f"{out_dir}/TRACK_A_LLM_REAL_ADAPTER_INTEGRATION_TEST_V1.md", "w", encoding="utf-8") as f:
    f.write(md_out)

# 5. VERIFY THE CANONICAL SCHEMA ITSELF
with open(f"{out_dir}/TRACK_A_ADJUDICATION_SCHEMA_FINAL_V1.json", "r", encoding="utf-8") as f:
    schema = json.load(f)

s_verify = []
s_verify.append("all 21 required fields exist: " + str(len(schema.get("required", [])) == 21))
s_verify.append("additionalProperties = false: " + str(schema.get("additionalProperties") is False))
props = schema.get("properties", {})
s_verify.append("proposed_label has exactly five labels: " + str(set(props.get("proposed_label", {}).get("enum", [])) == {"RELEVANT", "PARTIALLY_RELEVANT", "IRRELEVANT", "INSUFFICIENT_INFORMATION", "AMBIGUOUS"}))
s_verify.append("proposed_grade permits 0, 1, 2, null: " + str(set(props.get("proposed_grade", {}).get("enum", [])) == {0, 1, 2, None}))

alt_lbl = props.get("alternative_label_considered", {})
s_verify.append("alternative_label_considered nullable/enum: (Schema is currently type: [string, null], doesn't enforce enum on string explicitly without an enum list. We should check if enum exists)")
# Wait, I created alternative_label_considered as string/null previously but the user wants it to be STRICTLY the 5 labels or null.
# Let's verify it... Ah, it was NOT restricted to the enum in the previous script. Let's note it.
has_enum = "enum" in alt_lbl
s_verify.append(f"alternative_label_considered restricts enum: {has_enum}")

with open(f"{out_dir}/TRACK_A_LLM_CANONICAL_SCHEMA_VERIFY_V1.md", "w", encoding="utf-8") as f:
    f.write("# TRACK_A_LLM_CANONICAL_SCHEMA_VERIFY_V1\n")
    for line in s_verify: f.write(f"- {line}\n")

# 7 & 8: HASH VERIFICATIONS
with open(f"{out_dir}/TRACK_A_LLM_FINAL_SCHEMA_HASHES_V1.json", "r", encoding="utf-8") as f:
    stored_hashes = json.load(f)
    
calc_schema_hash = hashlib.sha256(json.dumps(schema, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
with open(f"{out_dir}/TRACK_A_LLM_ADJUDICATION_PROMPT_V2.txt", "rb") as f:
    calc_adj_hash = hashlib.sha256(f.read()).hexdigest()

hash_md = "# TRACK_A_LLM_HASH_VERIFICATION_V1\n"
hash_md += f"SCHEMA_HASH_MATCH = {'YES' if calc_schema_hash == stored_hashes.get('track_a_adjudication_schema_sha256') else 'NO'}\n"
hash_md += f"PROMPT_HASH_MATCH = {'YES' if calc_adj_hash == stored_hashes.get('adjudication_prompt_sha256') else 'NO'}\n"

with open(f"{out_dir}/TRACK_A_LLM_HASH_VERIFICATION_V1.md", "w", encoding="utf-8") as f:
    f.write(hash_md)
    
print("Integration tests and verifications complete.")
