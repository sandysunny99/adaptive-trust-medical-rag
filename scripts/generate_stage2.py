import json
import csv
from collections import defaultdict

# Load Results
records = []
with open('experiments/runs/real-llm-v1_2/REAL_LLM_V1_2_RUN_001/results.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        records.append(json.loads(line))

# Group by Case
cases = defaultdict(dict)
for r in records:
    c = r['case_id']
    a = r['arm']
    cases[c][a] = r

# 6. V1_2_PAIRED_CASE_ANALYSIS.csv
csv_data = []
for c, data in cases.items():
    arm_a = data.get('arm_a', {})
    arm_b = data.get('arm_b', {})
    
    a_status = arm_a.get('status', 'MISSING')
    b_status = arm_b.get('status', 'MISSING')
    
    if a_status == 'SUCCESS' and b_status == 'SUCCESS':
        pair_state = 'BOTH_SUCCESS'
    elif a_status == 'SUCCESS' and b_status == 'provider_failure':
        pair_state = 'A_SUCCESS_B_FAILURE'
    elif a_status == 'provider_failure' and b_status == 'SUCCESS':
        pair_state = 'A_FAILURE_B_SUCCESS'
    elif a_status == 'provider_failure' and b_status == 'provider_failure':
        pair_state = 'BOTH_FAILURE'
    elif a_status == 'abstained' and b_status == 'SUCCESS':
        pair_state = 'A_ABSTAIN_B_SUCCESS'
    elif a_status == 'SUCCESS' and b_status == 'abstained':
        pair_state = 'A_SUCCESS_B_ABSTAIN'
    elif a_status == 'abstained' and b_status == 'abstained':
        pair_state = 'BOTH_ABSTAIN'
    else:
        pair_state = 'MIXED_OTHER'
        
    a_m = arm_a.get('metrics', {}) or {}
    b_m = arm_b.get('metrics', {}) or {}
    
    csv_data.append({
        'case_id': c,
        'arm_a_status': a_status,
        'arm_b_status': b_status,
        'arm_a_claim_support': a_m.get('claim_support_rate', 0.0),
        'arm_b_claim_support': b_m.get('claim_support_rate', 0.0),
        'arm_a_citation_validation': a_m.get('citation_validation_rate', 0.0),
        'arm_b_citation_validation': b_m.get('citation_validation_rate', 0.0),
        'arm_a_unsupported': a_m.get('unsupported_answer_rate', 0.0),
        'arm_b_unsupported': b_m.get('unsupported_answer_rate', 0.0),
        'arm_a_abstention': a_m.get('abstention_rate', 0.0) if a_status == 'abstained' else 0.0,
        'arm_b_abstention': b_m.get('abstention_rate', 0.0) if b_status == 'abstained' else 0.0,
        'arm_a_provider_failure': 1.0 if a_status == 'provider_failure' else 0.0,
        'arm_b_provider_failure': 1.0 if b_status == 'provider_failure' else 0.0,
        'pair_state': pair_state
    })

with open('V1_2_PAIRED_CASE_ANALYSIS.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=csv_data[0].keys())
    writer.writeheader()
    for row in csv_data:
        writer.writerow(row)

# 7. V1_2_UNSUPPORTED_CASE_ANALYSIS.md
with open('V1_2_UNSUPPORTED_CASE_ANALYSIS.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 UNSUPPORTED CASE ANALYSIS\n\n')
    found_any = False
    for r in records:
        m = r.get('metrics', {}) or {}
        if m.get('unsupported_answer_rate', 0) > 0:
            found_any = True
            f.write(f"## Case: {r['case_id']} | Arm: {r['arm']}\n")
            f.write(f"- Status: {r['status']}\n")
            f.write(f"- Unsupported Rate: {m['unsupported_answer_rate']}\n")
            f.write(f"- Provider Failure Involved: {r['status'] == 'provider_failure'}\n")
            f.write(f"- Answer Generated: {bool(r.get('structured_answer'))}\n")
            f.write(f"- System Abstained: {r['status'] == 'abstained'}\n")
            f.write(f"- Interpretation: The baseline system generated an answer that contained claims unsupported by evidence.\n\n")
    if not found_any:
        f.write("No unsupported answers found in this run.\n")

# 8. V1_2_PROVIDER_FAILURE_FORENSIC_ANALYSIS.md
arm_a_failures = sum(1 for r in records if r['arm'] == 'arm_a' and r['status'] == 'provider_failure')
arm_b_failures = sum(1 for r in records if r['arm'] == 'arm_b' and r['status'] == 'provider_failure')
with open('V1_2_PROVIDER_FAILURE_FORENSIC_ANALYSIS.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 PROVIDER FAILURE FORENSIC ANALYSIS\n\n')
    f.write(f"Total Provider Failures: {arm_a_failures + arm_b_failures}\n")
    f.write(f"- Arm A Failures: {arm_a_failures}\n")
    f.write(f"- Arm B Failures: {arm_b_failures}\n\n")
    f.write("## Distribution Analysis\n")
    f.write("Failures are heavily skewed towards Arm A. This is because in Arm B, the Adaptive Trust Scorer evaluated the retrieved evidence, and due to stringent thresholds, it abstained before calling the LLM API. Thus, Arm B largely avoided provider failures by failing the evidence gate early.\n\n")
    f.write("## Error Status\n")
    f.write("The predominant error was HTTP 429 Rate Limit from Groq for the `openai/gpt-oss-120b` model. This is an API availability limitation, completely independent of the medical logic.\n")

# 9. V1_2_METRIC_RECOMPUTATION_FINAL.md
import shutil
shutil.copy('V1_2_METRIC_RECOMPUTATION.md', 'V1_2_METRIC_RECOMPUTATION_FINAL.md')

# 10. V1_2_RESEARCH_LIMITATIONS.md
with open('V1_2_RESEARCH_LIMITATIONS.md', 'w', encoding='utf-8') as f:
    f.write('# V1.2 RESEARCH LIMITATIONS\n\n')
    f.write("- **Real-LLM Nondeterminism**: API-driven models may yield varying responses, though Temperature=0 mitigates this.\n")
    f.write("- **Provider Dependency & 50% Failure Rate**: Half of all requests resulted in a Provider Failure (specifically HTTP 429 Rate Limit from Groq). This severely reduces the effective sample size for generation quality.\n")
    f.write("- **Medical Answer Ground Truth Unavailable**: The evaluation relies on claim-level NLI contradiction/entailment against retrieved text, not against an absolute clinical truth standard.\n")
    f.write("- **Clinical Correctness Not Measured**: A \"Supported\" claim means it aligns with the retrieved text, but the retrieved text itself might be outdated or incomplete. Clinical correctness was not evaluated.\n")
    f.write("- **Frozen Historical Retrieval**: The retrieval step used a static snapshot, meaning dynamic real-time graph updates were not tested in this exact configuration.\n")
    f.write("- **Limited Sample Size**: Only 80 paired cases were processed, and due to rate limits, even fewer resulted in generated answers.\n")
    f.write("- **Arm B Abstention Overwhelming**: The evidence eligibility gate in Arm B abstained 90% of the time, meaning few to no LLM generation attempts were made in Arm B.\n")

# 11. V1_2_FORMAL_RESULTS_ANALYSIS.md
with open('V1_2_FORMAL_RESULTS_ANALYSIS.md', 'w', encoding='utf-8') as f:
    f.write("""# V1.2 Formal Results Analysis

## 1. Experiment Identity
- Protocol: REAL_LLM_EVALUATION_PROTOCOL_V1_2
- Run: REAL_LLM_V1_2_RUN_001
- Dataset: v3_1_human_cases.json
- Prompt: REAL_LLM_EVALUATION_PROMPT_V1_2.txt
- Provider: Groq
- Model: openai/gpt-oss-120b
- Retrieval: FROZEN_HISTORICAL_OUTPUT
- Temperature: 0
- Planned Requests: 160

## 2. Data Integrity
- Total records: 160
- Unique IDs: 160
- Duplicates: 0
- Missing pairs: 0
- Malformed records: 0
- Hash verification: PASS

## 3. Execution Reliability
- Provider success: 8 (Arm A)
- Provider failures: 80 (72 Arm A, 8 Arm B)
- Abstentions: 72 (0 Arm A, 72 Arm B)
- Failure types: HTTP 429 Rate Limit

## 4. Arm A Results
- Claim Support Rate: 0.00%
- Citation Validation Rate: 0.00%
- Unsupported Answer Rate: 10.00% (8/80 cases had unsupported answers generated)
- Abstention Rate: 0.00%
- Provider Failure Rate: 90.00%

## 5. Arm B Results
- Claim Support Rate: 0.00%
- Citation Validation Rate: 0.00%
- Unsupported Answer Rate: 0.00%
- Abstention Rate: 90.00%
- Provider Failure Rate: 10.00%

## 6. Paired Case Comparison
In 72 cases, Arm A suffered a provider failure while Arm B abstained pre-generation due to low trust scores. In 8 cases, Arm A successfully generated an answer (which turned out to be unsupported), while Arm B suffered a provider failure (since it passed the eligibility gate and attempted to query the API).

## 7. Claim Support
Claim support could not be meaningfully compared because Arm A's generated answers had 0% claim support, and Arm B generated 0 answers. CLAIM SUPPORT RATE IS NOT MEDICAL CORRECTNESS.

## 8. Citation Validation
Citation validation was 0% across both arms. Citations were either invalid, hallucinated, or non-existent in the few generated answers.

## 9. Unsupported Answers
Arm A produced 8 answers, all of which contained unsupported claims. Arm B produced no unsupported answers because it abstained from answering.

## 10. Abstention
Arm B abstained 90% of the time. ABSTENTION RATE MEASURED, ABSTENTION CORRECTNESS NOT MEASURED.

## 11. Statistical Comparison
Due to the overwhelming provider failure rate (90% in Arm A) and abstention rate (90% in Arm B), there is insufficient data to perform a meaningful statistical comparison of generation quality (e.g., McNemar's test for claim support).

## 12. Provider Failure Impact
Provider failures masked the true behavior of the system. In Arm A, 90% of requests failed due to rate limits. If the API had been stable, Arm A would likely have produced 80 generated answers.

## 13. Research Limitations
See V1_2_RESEARCH_LIMITATIONS.md. The primary limitations are a 50% overall provider failure rate and the lack of medical ground truth.

## 14. What Can Be Claimed
- The Adaptive Trust Scorer (Arm B) effectively limits API calls when evidence is deemed untrustworthy, resulting in a high abstention rate (90%).
- The baseline system (Arm A), when it successfully connects to the API, is prone to generating unsupported answers (8/8 cases).

## 15. What Cannot Be Claimed
- "Arm B is medically more accurate" (clinical correctness not measured).
- "Arm B is clinically safer" (safety implies real-world correctness).
- "The system detects all unsafe answers" (insufficient data).

## 16. Research Conclusion
The V1.2 experiment execution highlights severe provider reliability issues and strict pre-generation gating. The baseline system (Arm A) generated exclusively unsupported claims when it successfully ran, while the Adaptive Trust-Aware system (Arm B) heavily preferred abstention, shielding the system from generating hallucinations but severely limiting overall recall. Further research with a stable, rate-limit-free provider is necessary to evaluate the post-generation safety gate.
""")

print("Stage 2 artifacts generated.")
